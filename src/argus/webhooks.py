from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import httpx
from pydantic import HttpUrl

from argus.config import Config

if TYPE_CHECKING:
	from argus.factcheck import FactCheck


async def _process_webhook(fact_check: FactCheck, client: httpx.AsyncClient, url: HttpUrl):
	try:
		# TODO: support things other than discord
		response = await client.post(url, json={
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
		                       					"inline": True
		                       				},
		                       				{
		                       					"name": "Completeness",
		                       					"value": f"{fact_check.completeness_score}/100",
		                       					"inline": True
		                       				},
		                       				{
		                       					"name": "Political Bias",
		                       					"value": f"{fact_check.political_score}/100",
		                       					"inline": True
		                       				},
		                       				{
		                       					"name": "Sensationalism",
		                       					"value": f"{fact_check.sensationalism_score}/100",
		                       					"inline": True
		                       				},
		                       				{
		                       					"name": "Emotional Language",
		                       					"value": f"{fact_check.emotional_language_score}/100",
		                       					"inline": True
		                       				}
		                       			],
		                       			"footer": {
		                       				"text": "Evaulated by ARGUS"
		                       			},
		                       			"timestamp": fact_check.fact_check_metadata["check_started"]
		                       		}
		                       	]
		                       })
	except:
		pass

async def process_webhooks(fact_check: FactCheck, config: Config):
    async with httpx.AsyncClient() as client:
    	asyncio.gather(
    		_process_webhook(fact_check, client, url) for url in config.webhooks
    	)
