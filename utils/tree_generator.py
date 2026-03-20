"""
Telegram RPG Bot - Family Tree Image Generator
=============================================
Generates visual family tree images using networkx and matplotlib.
"""

import logging
import io
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from database import db
from config import image_config

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of family tree nodes."""
    USER = "user"
    PARTNER = "partner"
    PARENT = "parent"
    CHILD = "child"
    GRANDPARENT = "grandparent"
    GRANDCHILD = "grandchild"


@dataclass
class FamilyNode:
    """Represents a node in the family tree."""
    user_id: int
    name: str
    username: str
    node_type: NodeType
    level: int  # Generation level (0 = user, -1 = parents, +1 = children)
    position: int = 0  # Horizontal position


class FamilyTreeGenerator:
    """Generates family tree visualizations."""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes: Dict[int, FamilyNode] = {}
        self.positions: Dict[int, Tuple[float, float]] = {}
        self.node_colors = {
            NodeType.USER: image_config.NODE_COLOR_USER,
            NodeType.PARTNER: image_config.NODE_COLOR_PARTNER,
            NodeType.PARENT: image_config.NODE_COLOR_PARENT,
            NodeType.CHILD: image_config.NODE_COLOR_CHILD,
            NodeType.GRANDPARENT: image_config.NODE_COLOR_GRANDPARENT,
            NodeType.GRANDCHILD: image_config.NODE_COLOR_GRANDCHILD,
        }
    
    async def fetch_family_data(self, user_id: int) -> Dict[str, Any]:
        """Fetch all family relationships from database."""
        user = db.users.find_one({"user_id": user_id})
        if not user:
            return {}
        
        family_data = {
            "user": user,
            "partner": None,
            "parents": [],
            "children": [],
            "grandparents": [],
            "grandchildren": [],
            "siblings": []
        }
        
        # Fetch partner
        if user.get("partner"):
            partner = db.users.find_one({"user_id": user["partner"]})
            if partner:
                family_data["partner"] = partner
        
        # Fetch parents
        for parent_id in user.get("parents", []):
            parent = db.users.find_one({"user_id": parent_id})
            if parent:
                family_data["parents"].append(parent)
                # Fetch grandparents
                for grandparent_id in parent.get("parents", []):
                    grandparent = db.users.find_one({"user_id": grandparent_id})
                    if grandparent:
                        family_data["grandparents"].append(grandparent)
        
        # Fetch children
        for child_id in user.get("children", []):
            child = db.users.find_one({"user_id": child_id})
            if child:
                family_data["children"].append(child)
                # Fetch grandchildren
                for grandchild_id in child.get("children", []):
                    grandchild = db.users.find_one({"user_id": grandchild_id})
                    if grandchild:
                        family_data["grandchildren"].append(grandchild)
        
        # Fetch siblings (other children of parents)
        for parent in family_data["parents"]:
            for sibling_id in parent.get("children", []):
                if sibling_id != user_id:
                    sibling = db.users.find_one({"user_id": sibling_id})
                    if sibling:
                        family_data["siblings"].append(sibling)
        
        return family_data
    
    def add_node(self, user_data: Dict[str, Any], node_type: NodeType, level: int) -> int:
        """Add a node to the graph."""
        user_id = user_data["user_id"]
        node = FamilyNode(
            user_id=user_id,
            name=user_data.get("name", "Unknown"),
            username=user_data.get("username", "unknown"),
            node_type=node_type,
            level=level
        )
        self.nodes[user_id] = node
        self.graph.add_node(user_id, node=node)
        return user_id
    
    def add_edge(self, from_id: int, to_id: int, edge_type: str = "parent") -> None:
        """Add an edge between nodes."""
        self.graph.add_edge(from_id, to_id, type=edge_type)
    
    def build_tree(self, family_data: Dict[str, Any]) -> None:
        """Build the family tree graph."""
        if not family_data.get("user"):
            return
        
        user_id = family_data["user"]["user_id"]
        
        # Add user node (center, level 0)
        self.add_node(family_data["user"], NodeType.USER, 0)
        
        # Add partner (level 0, next to user)
        if family_data["partner"]:
            partner_id = self.add_node(family_data["partner"], NodeType.PARTNER, 0)
            self.add_edge(user_id, partner_id, "marriage")
            self.add_edge(partner_id, user_id, "marriage")
        
        # Add parents (level -1)
        parent_positions = []
        for i, parent in enumerate(family_data["parents"]):
            parent_id = self.add_node(parent, NodeType.PARENT, -1)
            self.add_edge(parent_id, user_id, "parent")
            parent_positions.append((parent_id, i))
        
        # Add grandparents (level -2)
        grandparent_offset = 0
        for grandparent in family_data["grandparents"]:
            gp_id = self.add_node(grandparent, NodeType.GRANDPARENT, -2)
            # Connect to their child (parent)
            for parent in family_data["parents"]:
                if grandparent["user_id"] in parent.get("parents", []):
                    self.add_edge(gp_id, parent["user_id"], "parent")
            grandparent_offset += 1
        
        # Add children (level +1)
        for i, child in enumerate(family_data["children"]):
            child_id = self.add_node(child, NodeType.CHILD, 1)
            self.add_edge(user_id, child_id, "parent")
            
            # Add grandchildren (level +2)
            for grandchild in family_data["grandchildren"]:
                if grandchild["user_id"] in child.get("children", []):
                    gc_id = self.add_node(grandchild, NodeType.GRANDCHILD, 2)
                    self.add_edge(child_id, gc_id, "parent")
        
        # Add siblings (level 0)
        for sibling in family_data["siblings"]:
            sibling_id = self.add_node(sibling, NodeType.CHILD, 0)
            # Connect to shared parents
            for parent in family_data["parents"]:
                if sibling["user_id"] in parent.get("children", []):
                    self.add_edge(parent["user_id"], sibling_id, "parent")
    
    def calculate_positions(self) -> Dict[int, Tuple[float, float]]:
        """Calculate node positions for hierarchical layout."""
        if not self.nodes:
            return {}
        
        # Group nodes by level
        levels: Dict[int, List[int]] = {}
        for user_id, node in self.nodes.items():
            if node.level not in levels:
                levels[node.level] = []
            levels[node.level].append(user_id)
        
        # Sort nodes within each level
        for level in levels:
            levels[level].sort()
        
        # Calculate positions
        positions = {}
        y_spacing = 2.0  # Vertical spacing between generations
        x_spacing = 2.5  # Horizontal spacing between nodes
        
        for level, node_ids in levels.items():
            y = -level * y_spacing  # Negative because matplotlib y increases downward
            n_nodes = len(node_ids)
            total_width = (n_nodes - 1) * x_spacing
            start_x = -total_width / 2
            
            for i, node_id in enumerate(node_ids):
                x = start_x + i * x_spacing
                positions[node_id] = (x, y)
                self.nodes[node_id].position = i
        
        self.positions = positions
        return positions
    
    def draw_tree(self) -> plt.Figure:
        """Draw the family tree using matplotlib."""
        # Create figure with high resolution
        fig, ax = plt.subplots(figsize=(
            image_config.TREE_IMAGE_WIDTH / image_config.TREE_DPI,
            image_config.TREE_IMAGE_HEIGHT / image_config.TREE_DPI
        ), dpi=image_config.TREE_DPI)
        
        # Set background color
        fig.patch.set_facecolor('#f5f5f5')
        ax.set_facecolor('#f5f5f5')
        
        if not self.positions:
            ax.text(0.5, 0.5, "No family data available", 
                   ha='center', va='center', fontsize=20, transform=ax.transAxes)
            ax.axis('off')
            return fig
        
        # Draw edges
        for edge in self.graph.edges(data=True):
            from_id, to_id, data = edge
            if from_id in self.positions and to_id in self.positions:
                x1, y1 = self.positions[from_id]
                x2, y2 = self.positions[to_id]
                
                edge_type = data.get('type', 'parent')
                if edge_type == 'marriage':
                    # Draw marriage line (double line)
                    ax.plot([x1, x2], [y1, y2], 'r-', linewidth=3, alpha=0.7, zorder=1)
                    ax.plot([x1, x2], [y1, y2], 'pink', linewidth=1, alpha=0.9, zorder=1)
                else:
                    # Draw parent-child line
                    # Use curved lines for better aesthetics
                    mid_y = (y1 + y2) / 2
                    ax.plot([x1, x1], [y1, mid_y], '#2F4F4F', linewidth=2, zorder=1)
                    ax.plot([x1, x2], [mid_y, mid_y], '#2F4F4F', linewidth=2, zorder=1)
                    ax.plot([x2, x2], [mid_y, y2], '#2F4F4F', linewidth=2, zorder=1)
        
        # Draw nodes
        for user_id, pos in self.positions.items():
            node = self.nodes[user_id]
            color = self.node_colors.get(node.node_type, '#808080')
            
            # Draw node circle
            circle = plt.Circle(pos, 0.4, facecolor=color, edgecolor='black', 
                              linewidth=2, zorder=2)
            ax.add_patch(circle)
            
            # Add name text (truncated if too long)
            name = node.name[:10] + '...' if len(node.name) > 10 else node.name
            ax.text(pos[0], pos[1] + 0.1, name, ha='center', va='center',
                   fontsize=9, fontweight='bold', zorder=3)
            
            # Add username
            username = f"@{node.username[:8]}" if len(node.username) <= 8 else f"@{node.username[:8]}..."
            ax.text(pos[0], pos[1] - 0.15, username, ha='center', va='center',
                   fontsize=7, color='#666666', zorder=3)
        
        # Add legend
        legend_elements = [
            mpatches.Patch(facecolor=image_config.NODE_COLOR_USER, edgecolor='black', label='You'),
            mpatches.Patch(facecolor=image_config.NODE_COLOR_PARTNER, edgecolor='black', label='Partner'),
            mpatches.Patch(facecolor=image_config.NODE_COLOR_PARENT, edgecolor='black', label='Parent'),
            mpatches.Patch(facecolor=image_config.NODE_COLOR_CHILD, edgecolor='black', label='Child'),
            mpatches.Patch(facecolor=image_config.NODE_COLOR_GRANDPARENT, edgecolor='black', label='Grandparent'),
            mpatches.Patch(facecolor=image_config.NODE_COLOR_GRANDCHILD, edgecolor='black', label='Grandchild'),
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=8, 
                 framealpha=0.9, title='Family Members')
        
        # Set title
        user_node = self.nodes.get(list(self.nodes.keys())[0]) if self.nodes else None
        title = f"Family Tree - {user_node.name}" if user_node else "Family Tree"
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        # Set axis properties
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Set limits with padding
        if self.positions:
            x_vals = [p[0] for p in self.positions.values()]
            y_vals = [p[1] for p in self.positions.values()]
            padding = 2
            ax.set_xlim(min(x_vals) - padding, max(x_vals) + padding)
            ax.set_ylim(min(y_vals) - padding, max(y_vals) + padding)
        
        plt.tight_layout()
        return fig
    
    def to_image(self) -> io.BytesIO:
        """Convert the tree to PNG image bytes."""
        fig = self.draw_tree()
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=image_config.TREE_DPI, 
                   bbox_inches='tight', facecolor='#f5f5f5')
        buf.seek(0)
        
        plt.close(fig)
        return buf
    
    async def generate(self, user_id: int) -> Optional[io.BytesIO]:
        """Generate family tree image for user."""
        try:
            # Fetch family data
            family_data = await self.fetch_family_data(user_id)
            if not family_data:
                return None
            
            # Build tree
            self.build_tree(family_data)
            
            # Calculate positions
            self.calculate_positions()
            
            # Generate image
            return self.to_image()
            
        except Exception as e:
            logger.error(f"Error generating family tree: {e}")
            return None


async def generate_family_tree(user_id: int) -> Optional[io.BytesIO]:
    """
    Generate a family tree image for the specified user.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        BytesIO object containing PNG image, or None if generation fails
    """
    generator = FamilyTreeGenerator()
    return await generator.generate(user_id)


class FullFamilyTreeGenerator(FamilyTreeGenerator):
    """Extended generator for full family tree with all extended relatives."""
    
    async def fetch_extended_family(self, user_id: int) -> Dict[str, Any]:
        """Fetch extended family including aunts, uncles, cousins."""
        family_data = await self.fetch_family_data(user_id)
        
        # Add extended family containers
        family_data["aunts_uncles"] = []
        family_data["cousins"] = []
        family_data["nieces_nephews"] = []
        
        # Fetch aunts/uncles (siblings of parents)
        for parent in family_data.get("parents", []):
            for sibling_id in parent.get("siblings", []):
                if sibling_id not in [p["user_id"] for p in family_data["parents"]]:
                    aunt_uncle = db.users.find_one({"user_id": sibling_id})
                    if aunt_uncle:
                        family_data["aunts_uncles"].append(aunt_uncle)
                        # Fetch cousins (children of aunts/uncles)
                        for cousin_id in aunt_uncle.get("children", []):
                            cousin = db.users.find_one({"user_id": cousin_id})
                            if cousin:
                                family_data["cousins"].append(cousin)
        
        # Fetch nieces/nephews (children of siblings)
        for sibling in family_data.get("siblings", []):
            for nn_id in sibling.get("children", []):
                nn = db.users.find_one({"user_id": nn_id})
                if nn:
                    family_data["nieces_nephews"].append(nn)
        
        return family_data
    
    def build_extended_tree(self, family_data: Dict[str, Any]) -> None:
        """Build extended family tree."""
        # Build basic tree first
        self.build_tree(family_data)
        
        # Add aunts/uncles (level -1, extended horizontally)
        for aunt_uncle in family_data.get("aunts_uncles", []):
            au_id = self.add_node(aunt_uncle, NodeType.PARENT, -1)
            # Connect to their parents (user's grandparents)
            for parent in family_data.get("parents", []):
                if aunt_uncle["user_id"] in parent.get("siblings", []):
                    for gp in family_data.get("grandparents", []):
                        if parent["user_id"] in gp.get("children", []):
                            self.add_edge(gp["user_id"], au_id, "parent")
        
        # Add cousins (level 0, extended)
        for cousin in family_data.get("cousins", []):
            cousin_id = self.add_node(cousin, NodeType.CHILD, 0)
            # Connect to their parents (user's aunts/uncles)
            for au in family_data.get("aunts_uncles", []):
                if cousin["user_id"] in au.get("children", []):
                    self.add_edge(au["user_id"], cousin_id, "parent")
    
    async def generate_full(self, user_id: int) -> Optional[io.BytesIO]:
        """Generate full extended family tree."""
        try:
            family_data = await self.fetch_extended_family(user_id)
            if not family_data:
                return None
            
            self.build_extended_tree(family_data)
            self.calculate_positions()
            return self.to_image()
            
        except Exception as e:
            logger.error(f"Error generating full family tree: {e}")
            return None


async def generate_full_family_tree(user_id: int) -> Optional[io.BytesIO]:
    """
    Generate a full extended family tree image.
    
    Args:
        user_id: The Telegram user ID
        
    Returns:
        BytesIO object containing PNG image, or None if generation fails
    """
    generator = FullFamilyTreeGenerator()
    return await generator.generate_full(user_id)
