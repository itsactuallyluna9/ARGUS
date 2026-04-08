from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx
from loguru import logger
from pydantic import HttpUrl

from argus.config import Config

if TYPE_CHECKING:
    from argus.factcheck import FactCheck


def _detect_webhook_service(url: str) -> str:
    """Detect the webhook service type from URL."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    if "discord" in domain:
        return "discord"
    elif "slack" in domain:
        return "slack"
    elif "ntfy" in domain:
        return "ntfy"
    else:
        return "generic"


def _build_discord_payload(fact_check: FactCheck) -> dict:
    """Build a Discord webhook payload."""
    return {
        "username": "ARGUS",
        "content": None,
        "embeds": [
            {
                "title": fact_check.article_metadata["title"] or "No Title",
                "description": fact_check.summary,
                "url": f"http://localhost:5174/details/{fact_check.id}",
                "color": 5814783,
                "fields": [
                    {
                        "name": "Accuracy",
                        "value": f"{fact_check.accuracy_score}/100",
                        "inline": True,
                    },
                    {
                        "name": "Completeness",
                        "value": f"{fact_check.completeness_score}/100",
                        "inline": True,
                    },
                    {
                        "name": "Political Bias",
                        "value": f"{fact_check.political_score}/100",
                        "inline": True,
                    },
                    {
                        "name": "Sensationalism",
                        "value": f"{fact_check.sensationalism_score}/100",
                        "inline": True,
                    },
                    {
                        "name": "Emotional Language",
                        "value": f"{fact_check.emotional_language_score}/100",
                        "inline": True,
                    },
                ],
                "footer": {"text": "Evaluated by ARGUS"},
                "timestamp": fact_check.fact_check_metadata["check_started"],
            }
        ],
    }


def _build_slack_payload(fact_check: FactCheck) -> dict:
    """Build a Slack webhook payload."""
    return {
        "username": "ARGUS",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": fact_check.article_metadata["title"] or "No Title",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary*\n{fact_check.summary}\n\n<http://localhost:5174/details/{fact_check.id}|View Full Report>",
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Accuracy*\n{fact_check.accuracy_score}/100",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Completeness*\n{fact_check.completeness_score}/100",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Political Bias*\n{fact_check.political_score}/100",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Sensationalism*\n{fact_check.sensationalism_score}/100",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Emotional Language*\n{fact_check.emotional_language_score}/100",
                    },
                ],
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Evaluated by ARGUS at {fact_check.fact_check_metadata['check_started']}",
                    }
                ],
            },
        ],
    }


def _build_ntfy_payload(fact_check: FactCheck) -> tuple[str, dict]:
    """Build an ntfy.sh payload. Returns (text_content, headers)."""
    text = (
        f"✓ ARGUS Fact Check Complete\n\n"
        f"Title: {fact_check.article_metadata['title'] or 'No Title'}\n\n"
        f"Accuracy: {fact_check.accuracy_score}/100\n"
        f"Completeness: {fact_check.completeness_score}/100\n"
        f"Political Bias: {fact_check.political_score}/100\n"
        f"Sensationalism: {fact_check.sensationalism_score}/100\n"
        f"Emotional Language: {fact_check.emotional_language_score}/100\n\n"
        f"View Report: http://localhost:5174/details/{fact_check.id}"
    )
    headers = {
        "Title": "ARGUS Fact Check Complete",
        "Priority": "default",
        "Tags": "argus,factcheck",
    }
    return text, headers


async def _process_webhook(
    fact_check: FactCheck, client: httpx.AsyncClient, url: HttpUrl
):
    try:
        service = _detect_webhook_service(str(url))

        if service == "discord":
            payload = _build_discord_payload(fact_check)
            response = await client.post(str(url), json=payload)
        elif service == "slack":
            payload = _build_slack_payload(fact_check)
            response = await client.post(str(url), json=payload)
        elif service == "ntfy":
            text, headers = _build_ntfy_payload(fact_check)
            response = await client.post(str(url), content=text, headers=headers)
        else:
            # Generic JSON payload - send the full fact_check.to_dict()
            payload = fact_check.to_dict()
            response = await client.post(str(url), json=payload)

        logger.debug(
            "Got {status_code} for webhook {hook}",
            status_code=response.status_code,
            hook=url,
        )
    except Exception as e:
        logger.exception(e)


async def process_webhooks(fact_check: FactCheck, config: Config):
    logger.info("Sending webhooks! URLs: {}", config.webhooks)
    if not config.webhooks:
        logger.warning("No webhook URLs configured, skipping")
        return
    async with httpx.AsyncClient() as client:
        await asyncio.gather(
            *[_process_webhook(fact_check, client, url) for url in config.webhooks]
        )
    logger.info("All webhooks processed")
