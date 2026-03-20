# Telegram RPG Bot

A comprehensive Telegram RPG simulation bot featuring a complete family tree system, economy, crime, factory management, farming, and mini-games.

## Features

### Core Features
- **User Profiles** - Track money, bank, level, experience, reputation
- **Family System** - Marry, adopt children, build family trees
- **Family Tree Visualization** - Generate PNG images of your family tree
- **Friend System** - Add friends, view friend circles

### Economy System
- **Daily Rewards** - Claim daily rewards with streak bonuses
- **Bank System** - Deposit/withdraw with interest
- **Jobs** - Work different jobs for income
- **Shop** - Buy tools, consumables, pets, accessories
- **Loans** - Take loans with repayment system

### Crime System
- **Robbery** - Rob other users (with jail risk)
- **Attacks** - Attack other users
- **Weapons** - Buy weapons for criminal activities
- **Insurance** - Protect yourself from crimes
- **Jail System** - Get caught and serve time or pay bail

### Factory System
- **Own Factories** - Generate passive income
- **Hire Workers** - Increase production
- **Upgrades** - Improve factory efficiency

### Garden/Farming System
- **Plant Crops** - Grow various crops
- **Harvest** - Sell crops for profit
- **Fertilize** - Speed up growth
- **Weather** - Weather affects crop growth

### Market System
- **Market Stands** - List items for sale
- **Trading** - Trade with other users
- **Gifting** - Gift items to friends

### Games
- **Dice** - Roll and win
- **Slots** - Slot machine
- **Blackjack** - Card game
- **Guess** - Number guessing
- **Trivia** - Quiz questions
- **Lottery** - Buy tickets and win jackpot

### Leaderboards
- **Level Board** - Top players by level
- **Money Board** - Richest players
- **Family Board** - Top families
- **Factory Board** - Top factories

## Tech Stack

- **Language**: Python 3.11+
- **Telegram Framework**: python-telegram-bot (async)
- **Database**: MongoDB with pymongo
- **Image Processing**: Pillow
- **Graph Generation**: networkx, matplotlib
- **Scheduler**: APScheduler

## Installation

### Prerequisites
- Python 3.11 or higher
- MongoDB server
- Telegram Bot Token (from @BotFather)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd telegram_rpg_bot
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Step 5: Start MongoDB
Make sure MongoDB is running on your system.

### Step 6: Run the Bot
```bash
python bot.py
```

## Configuration

Edit the `.env` file with your settings:

```env
BOT_TOKEN=your_bot_token_here
BOT_USERNAME=your_bot_username
ADMIN_IDS=your_telegram_id
MONGO_URI=mongodb://localhost:27017
DB_NAME=telegram_rpg_bot
```

## Commands

### Core Commands
- `/start` - Start the bot and create profile
- `/help` - Show help menu
- `/profile` - View your profile
- `/settings` - Bot settings
- `/stats` - Your statistics
- `/activity` - Your activity log

### Family Commands
- `/family` - Family information
- `/tree` - View family tree (text)
- `/fulltree` - View family tree (image)
- `/adopt` - Adopt a child
- `/marry` - Marry someone
- `/divorce` - Divorce your partner
- `/disown` - Disown a child
- `/relations` - View relationships
- `/parents` - View your parents
- `/children` - View your children

### Friends Commands
- `/friend` - Add a friend
- `/unfriend` - Remove a friend
- `/friends` - Your friends list
- `/circle` - Your friend circle
- `/suggestions` - Friend suggestions
- `/ratings` - Friend ratings

### Economy Commands
- `/daily` - Claim daily reward
- `/account` - Bank account info
- `/pay` - Pay someone
- `/deposit` - Deposit to bank
- `/withdraw` - Withdraw from bank
- `/job` - View/change job
- `/work` - Work for money
- `/shop` - View shop
- `/buy` - Buy item
- `/sell` - Sell item
- `/inventory` - Your inventory
- `/balance` - Check balance
- `/transfer` - Transfer money
- `/loan` - Take a loan
- `/repay` - Repay loan
- `/bank` - Bank operations

### Crime Commands
- `/rob` - Rob someone
- `/kill` - Attack someone
- `/weapon` - Your weapons
- `/buyweapon` - Buy weapon
- `/insurance` - Insurance info
- `/medical` - Medical services
- `/jail` - Jail status
- `/bail` - Pay bail

### Factory Commands
- `/factory` - Your factory
- `/hire` - Hire workers
- `/fire` - Fire workers
- `/workers` - Your workers
- `/production` - Factory production
- `/factoryupgrade` - Upgrade factory

### Garden Commands
- `/garden` - Your garden
- `/add` - Add plot to garden
- `/plant` - Plant seeds
- `/harvest` - Harvest crops
- `/fertilise` - Fertilise crops
- `/barn` - Your barn
- `/orders` - View orders
- `/seeds` - Your seeds
- `/weather` - Weather forecast

### Market Commands
- `/stand` - Your market stand
- `/stands` - View all stands
- `/putstand` - Put item for sale
- `/trade` - Trade with someone
- `/gift` - Gift item
- `/auction` - View auctions
- `/bid` - Place bid

### Games Commands
- `/fourpics` - 4 Pics 1 Word game
- `/ripple` - Ripple game
- `/lottery` - Buy lottery ticket
- `/nation` - Nation guessing
- `/quiz` - Quiz game
- `/dice` - Dice game
- `/blackjack` - Blackjack
- `/slots` - Slot machine
- `/guess` - Number guessing
- `/trivia` - Trivia game

### Leaderboard Commands
- `/leaderboard` - Top players
- `/moneyboard` - Richest players
- `/familyboard` - Top families
- `/factoryboard` - Top factories
- `/moneygraph` - Money history graph

### Admin Commands
- `/ban` - Ban a user
- `/unban` - Unban a user
- `/broadcast` - Broadcast message
- `/adminstats` - Bot statistics
- `/logs` - View logs

## Family Tree Image Generator

The bot includes a powerful family tree image generator that creates visual representations of family relationships:

- Shows user, partner, parents, children, grandparents, grandchildren
- Color-coded nodes for different relationship types
- Hierarchical layout for clear visualization
- Generated as PNG images

Usage: `/fulltree` or `/fulltree <user_id>`

## Database Schema

### Collections
- `users` - User profiles and data
- `families` - Family groups
- `friends` - Friend relationships
- `inventory` - User inventories
- `economy` - Economy data
- `gardens` - Garden data
- `factory` - Factory data
- `market` - Market listings
- `games` - Game data
- `stats` - User statistics
- `logs` - Activity logs

## Project Structure

```
telegram_rpg_bot/
├── bot.py                 # Main bot application
├── config.py              # Configuration settings
├── database.py            # Database connection and operations
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment file
├── README.md             # This file
├── modules/
│   ├── core/             # Core commands
│   ├── family/           # Family system
│   ├── friends/          # Friend system
│   ├── economy/          # Economy system
│   ├── crime/            # Crime system
│   ├── factory/          # Factory system
│   ├── garden/           # Garden/farming system
│   ├── market/           # Market system
│   ├── games/            # Mini-games
│   ├── stats/            # Leaderboards
│   └── admin/            # Admin commands
└── utils/
    ├── tree_generator.py # Family tree image generator
    ├── image_tools.py    # Image processing utilities
    ├── cooldown.py       # Cooldown management
    ├── helpers.py        # Helper functions
    ├── validators.py     # Input validation
    ├── timers.py         # Timer management
    └── logger.py         # Logging configuration
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For support, join our Telegram group or contact the developers.

---

**Enjoy the game!** 🎮
