# Chat Training Data

This folder stores chat examples and conversation patterns that the AI uses to learn how to talk.

## Structure

- **examples/** - Sample conversations to learn from
- **learned/** - Auto-generated learned patterns from real Telegram chats
- **templates/** - Conversation templates and formats

## How to Add Training Data

### Method 1: Manual Examples
Create `.txt` or `.json` files with example conversations:

**Format (conversation.txt):**
```
CUSTOMER: Hey, do you have databases?
BOT: Yeah, we got premium crypto databases. What you looking for?
CUSTOMER: Bitcoin addresses database
BOT: That'll run you $500 in BTC or ETH. Got wallet?
```

### Method 2: Auto-Learn from Telegram
The bot automatically:
1. Saves all customer conversations to `learned/`
2. Analyzes tone, style, responses
3. Updates the personality model
4. Learns pricing patterns

### Method 3: Export & Share Chats
You can:
- Export Telegram chats as JSON
- Place in `examples/` folder
- Bot will parse and learn patterns

## Bot Learning Process

1. **Collects** all conversations
2. **Analyzes** response patterns
3. **Extracts** common phrases/tone
4. **Updates** system prompt dynamically
5. **Improves** over time with new chats
