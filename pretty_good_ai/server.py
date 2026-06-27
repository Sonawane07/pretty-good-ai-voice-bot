from __future__ import annotations

import asyncio
import json
import logging

import websockets
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from twilio.twiml.voice_response import Connect, Say, Stream, VoiceResponse

from pretty_good_ai.config import ConfigError, load_settings
from pretty_good_ai.scenarios import get_scenario, realtime_instructions

app = FastAPI(title="Pretty Good AI Voice Bot")
logger = logging.getLogger(__name__)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/scenario/{scenario_id}")
def scenario_details(scenario_id: str) -> dict[str, str | None]:
    scenario = get_scenario(scenario_id)
    return {
        "id": scenario.id,
        "title": scenario.title,
        "goal": scenario.goal,
        "details": scenario.details,
        "edge_case": scenario.edge_case,
    }


@app.api_route("/voice/twiml", methods=["GET", "POST"])
async def voice_twiml(request: Request) -> Response:
    settings = load_settings()
    scenario_id = request.query_params.get("scenario_id", "call-01")
    scenario = get_scenario(scenario_id)

    response = VoiceResponse()
    response.say(
        "Connecting you now.",
        voice="alice",
    )
    connect = Connect()
    stream = Stream(url=settings.media_stream_url)
    stream.parameter(name="scenario_id", value=scenario.id)
    connect.append(stream)
    response.append(connect)
    return Response(content=str(response), media_type="application/xml")


@app.post("/voice/recording-status")
async def recording_status(request: Request) -> dict[str, str]:
    form = await request.form()
    call_sid = str(form.get("CallSid", ""))
    recording_sid = str(form.get("RecordingSid", ""))
    recording_url = str(form.get("RecordingUrl", ""))
    logger.info("Recording ready call_sid=%s recording_sid=%s url=%s", call_sid, recording_sid, recording_url)
    return {"status": "received"}


@app.websocket("/voice/media")
async def voice_media(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        settings = load_settings()
        await _bridge_twilio_to_openai(websocket, settings)
    except WebSocketDisconnect:
        logger.info("Twilio media websocket disconnected")
    except ConfigError as exc:
        logger.error("Configuration error in media websocket: %s", exc)
        await websocket.close(code=1011)


async def _bridge_twilio_to_openai(websocket: WebSocket, settings) -> None:
    openai_url = f"wss://api.openai.com/v1/realtime?model={settings.openai_realtime_model}"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "OpenAI-Safety-Identifier": "pretty-good-ai-challenge-local",
    }

    async with websockets.connect(openai_url, additional_headers=headers) as openai_ws:
        stream_sid_holder: dict[str, str] = {}
        scenario_id_holder = {"scenario_id": "call-01"}
        initial_response_sent = {"sent": False}

        await _send_session_update(openai_ws, scenario_id_holder["scenario_id"], settings.openai_realtime_model)

        async def from_twilio() -> None:
            async for message_text in websocket.iter_text():
                message = json.loads(message_text)
                event = message.get("event")

                if event == "start":
                    start = message.get("start", {})
                    stream_sid_holder["stream_sid"] = start.get("streamSid", "")
                    params = start.get("customParameters", {}) or {}
                    scenario_id_holder["scenario_id"] = params.get("scenario_id", "call-01")
                    await _send_session_update(
                        openai_ws,
                        scenario_id_holder["scenario_id"],
                        settings.openai_realtime_model,
                    )
                    if not initial_response_sent["sent"]:
                        await _send_initial_response(openai_ws)
                        initial_response_sent["sent"] = True
                    logger.info("Media stream started scenario=%s", scenario_id_holder["scenario_id"])

                elif event == "media":
                    payload = message.get("media", {}).get("payload")
                    if payload:
                        await openai_ws.send(
                            json.dumps(
                                {
                                    "type": "input_audio_buffer.append",
                                    "audio": payload,
                                }
                            )
                        )

                elif event == "stop":
                    logger.info("Media stream stopped")
                    await openai_ws.close()
                    break

        async def from_openai() -> None:
            async for message_text in openai_ws:
                message = json.loads(message_text)
                msg_type = message.get("type")

                if msg_type in {"response.output_audio.delta", "response.audio.delta", "output_audio_buffer.delta"}:
                    delta = message.get("delta")
                    stream_sid = stream_sid_holder.get("stream_sid")
                    if delta and stream_sid:
                        await websocket.send_json(
                            {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {"payload": delta},
                            }
                        )

                elif msg_type == "input_audio_buffer.speech_started":
                    stream_sid = stream_sid_holder.get("stream_sid")
                    if stream_sid:
                        await websocket.send_json({"event": "clear", "streamSid": stream_sid})

                elif msg_type == "error":
                    logger.error("OpenAI realtime error: %s", message)

        try:
            await asyncio.gather(from_twilio(), from_openai())
        except websockets.exceptions.ConnectionClosed as exc:
            logger.warning("OpenAI realtime websocket closed: code=%s reason=%s", exc.code, exc.reason)


async def _send_session_update(openai_ws, scenario_id: str, model: str) -> None:
    scenario = get_scenario(scenario_id)
    await openai_ws.send(
        json.dumps(
            {
                "type": "session.update",
                "session": {
                    "type": "realtime",
                    "model": model,
                    "output_modalities": ["audio"],
                    "instructions": realtime_instructions(scenario),
                    "audio": {
                        "input": {
                            "format": {
                                "type": "audio/pcmu",
                            },
                            "turn_detection": {
                                "type": "server_vad",
                                "threshold": 0.5,
                                "prefix_padding_ms": 300,
                                "silence_duration_ms": 700,
                                "create_response": True,
                                "interrupt_response": True,
                            },
                        },
                        "output": {
                            "format": {
                                "type": "audio/pcmu",
                            },
                            "voice": "marin",
                        },
                    },
                },
            }
        )
    )


async def _send_initial_response(openai_ws) -> None:
    await openai_ws.send(
        json.dumps(
            {
                "type": "response.create",
                "response": {
                    "output_modalities": ["audio"],
                    "instructions": (
                        "Start the phone call as the patient. Say hello, give your name briefly, "
                        "and state the scenario goal in a natural way. Keep it under two sentences."
                    ),
                },
            }
        )
    )
