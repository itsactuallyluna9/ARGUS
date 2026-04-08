# Using Webhooks

ARGUS can notify you when a fact-check completes by sending a webhook to a URL of your choice. This is particularly useful for long-running analyses, allowing you to be notified without having to keep the page open.

## Supported Services

ARGUS automatically detects the webhook service from the URL and formats the payload accordingly:

- **Discord** - Sends embed messages with the fact-check results (rich formatting)
- **Slack** - Sends formatted block messages with key metrics and summary
- **ntfy.sh** - Sends simple text notifications optimized for mobile
- **Generic/Custom** - Posts the complete fact-check data as JSON

Service detection is automatic based on the webhook URL domain.

## Configuration

To enable webhooks, add them to your `config.toml` file:

```toml
webhooks = [
    "https://discordapp.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN",
    "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    "https://ntfy.sh/your-topic-name"
]
```

You can add multiple webhooks and they will all be triggered when a fact-check completes.

## Webhook Payload Format

When a fact-check completes, ARGUS sends a POST request to each configured webhook URL. The format depends on the service detected from the URL.

### Discord

Discord webhooks receive formatted embed messages with key metrics:

```json
{
    "username": "ARGUS",
    "content": null,
    "embeds": [
        {
            "title": "Article Title",
            "description": "Article summary...",
            "url": "http://localhost:5174/details/{fact_check_id}",
            "color": 5814783,
            "fields": [
                {
                    "name": "Accuracy",
                    "value": "85/100",
                    "inline": true
                },
                {
                    "name": "Completeness",
                    "value": "72/100",
                    "inline": true
                },
                {
                    "name": "Political Bias",
                    "value": "45/100",
                    "inline": true
                },
                {
                    "name": "Sensationalism",
                    "value": "38/100",
                    "inline": true
                },
                {
                    "name": "Emotional Language",
                    "value": "41/100",
                    "inline": true
                }
            ],
            "footer": {
                "text": "Evaluated by ARGUS"
            },
            "timestamp": "2026-04-08T12:00:00Z"
        }
    ]
}
```

### Slack

Slack webhooks receive block-formatted messages optimized for the Slack interface:

```json
{
    "username": "ARGUS",
    "blocks": [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Article Title",
                "emoji": true
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Summary*\nArticle summary text...\n\n<http://localhost:5174/details/{fact_check_id}|View Full Report>"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Accuracy*\n85/100"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Completeness*\n72/100"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Political Bias*\n45/100"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Sensationalism*\n38/100"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Emotional Language*\n41/100"
                }
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Evaluated by ARGUS at 2026-04-08T12:00:00Z"
                }
            ]
        }
    ]
}
```

> [!WARNING]
> The authors don't use Slack, and therefore haven't tested if this works as intended. 

### ntfy.sh

ntfy.sh webhooks receive plain-text notifications optimized for mobile delivery:

```
✓ ARGUS Fact Check Complete

Title: Article Title

Accuracy: 85/100
Completeness: 72/100
Political Bias: 45/100
Sensationalism: 38/100
Emotional Language: 41/100

View Report: http://localhost:5174/details/{fact_check_id}
```

Headers include:
- `Title`: "ARGUS Fact Check Complete"
- `Priority`: "default"
- `Tags`: "argus,factcheck"

### Generic/Custom Endpoints

For any other URL, ARGUS posts the complete fact-check data as JSON (same as what the frontend receives):

```json
{
    "url": "https://example.com/article",
    "id": "fact_check_id_here",
    "fact_check_metadata": {
        "check_submitted": "2026-04-08T12:00:00Z",
        "check_started": "2026-04-08T12:00:05Z",
        "check_finished": "2026-04-08T12:05:30Z",
        "check_duration_from_start": 325.5,
        "check_duration_from_submitted": 330.2,
        "scraper_duration": 2.3,
        "summary_duration": 8.1,
        "agents_duration": 15.3
    },
    "article_text": "Full article content...",
    "summary": "Concise summary...",
    "bias_rating": "Any potential biases... (use the more specific versions)",
    "key_points": ["Point 1", "Point 2"],
    "article_metadata": {
        "title": "Article Title",
        "url": "https://example.com/article",
        "source": "Example News",
        "publish_date": "2026-04-08"
    },
    "accuracy_score": 85,
    "completeness_score": 72,
    "accuracy_explanation": "Most claims are supported by sources...",
    "completeness_explanation": "Missing some important perspectives...",
    "accuracy_sources": [...],
    "completeness_sources": [...],
    "political_bias": "Explanation of any political bias....",
    "sensationalism": "Explanation of how exadaggedarated it is...",
    "emotional_language": "Explanation of any emotional language used...",
    "political_score": 35,
    "sensationalism_score": 38,
    "emotional_language_score": 41,
    "finished": true
}
```

## Programmatic Submission

You can also submit URLs to fact-check programmatically by sending a POST request to ARGUS:

```bash
curl -X POST http://localhost:5000/api/factcheck \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com/article"}'
```

The response will include a `id` that you can use to track the analysis.

## Bookmarklet

To quickly submit the current article you're reading, you can create a bookmarklet. Add this as a new bookmark in your browser:

```javascript
javascript:(function(){fetch('http://localhost:5000/api/factcheck',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:window.location.href})}).then(r=>r.json()).then(d=>alert('Fact check started! ID: '+d.id))})()
```

Replace `http://localhost:5000` with your ARGUS server URL if running remotely.

> [!WARNING]
> ARGUS currently has no rate limits, and no queue system. If submitting many URLs via webhook API, the system can become overloaded.
