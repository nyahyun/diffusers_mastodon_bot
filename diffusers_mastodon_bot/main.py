import logging
import sys
from pathlib import Path
from typing import *
import json

from mastodon import Mastodon

import torch

from diffusers.pipelines.stable_diffusion import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline

from diffusers_mastodon_bot.app_stream_listener import AppStreamListener
from diffusers_mastodon_bot.bot_request_handlers.bot_request_handler import BotRequestHandler
from diffusers_mastodon_bot.bot_request_handlers.game.diffuse_game_handler import DiffuseGameHandler
from diffusers_mastodon_bot.bot_request_handlers.diffuse_me_handler import DiffuseMeHandler
from diffusers_mastodon_bot.bot_request_handlers.diffuse_it_handler import DiffuseItHandler
from pipelines.stable_diffusion.safety_checker_dummy import StableDiffusionSafetyCheckerDummy


def create_diffusers_pipeline(device_name='cuda'):
    pipe: StableDiffusionPipeline = StableDiffusionPipeline.from_pretrained(
        # "CompVis/stable-diffusion-v1-4",
        'hakurei/waifu-diffusion',
        revision='fp16',
        torch_dtype=torch.float16,
        use_auth_token=True,
        safety_checker=StableDiffusionSafetyCheckerDummy(),
    )  # type: ignore

    pipe = pipe.to(device_name)
    pipe.enable_attention_slicing()
    return pipe

def pipe_as_img2img(pipe):
    pipe_img2img = StableDiffusionImg2ImgPipeline(
        text_encoder=pipe.text_encoder,
        tokenizer=pipe.tokenizer,
        feature_extractor=pipe.feature_extractor,
        vae=pipe.vae,
        unet=pipe.unet,
        scheduler=pipe.scheduler,
        safety_checker=pipe.safety_checker,
    )
    
    pipe_img2img = pipe_img2img.to(pipe.device)
    pipe_img2img.enable_attention_slicing()
    return pipe_img2img

def read_text_file(filename: str) -> Union[str, None]:
    path = Path(filename)
    if not Path(filename).is_file():
        return None

    content = path.read_text(encoding='utf8').strip()
    if len(content) == 0:
        return None

    return content


def load_json_dict(filename: str) -> Union[None, Dict[str, Any]]:
    result = read_text_file(filename)
    if result is not None:
        return json.loads(result)
    else:
        return None


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("diffusers_mastodon_bot.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

    access_token = read_text_file('./config/access_token.txt')
    endpoint_url = read_text_file('./config/endpoint_url.txt')

    if access_token is None:
        print('mastodon access token is required but not found. check ./config/access_token.txt')
        exit()

    if access_token is None:
        print('mastodon endpoint url is required but not found. check ./config/endpoint_url.txt')
        exit()

    toot_listen_start = read_text_file('./config/toot_listen_start.txt')
    toot_listen_end = read_text_file('./config/toot_listen_end.txt')
    toot_listen_start_cw = read_text_file('./config/toot_listen_start_cw.txt')

    proc_kwargs = load_json_dict('./config/proc_kwargs.json')
    app_stream_listener_kwargs = load_json_dict('./config/app_stream_listener_kwargs.json')
    if app_stream_listener_kwargs is None:
        app_stream_listener_kwargs = {}

    diffusion_game_messages = load_json_dict('./config/diffusion_game_messages.json')

    logging.info('starting')
    mastodon = Mastodon(
        access_token=access_token,
        api_base_url=endpoint_url
    )

    logging.info('info checking')
    account = mastodon.account_verify_credentials()
    my_url = account['url']
    my_acct = account['acct']
    logging.info(f'you are, acct: {my_acct} / url: {my_url}')

    logging.info('loading model')
    device_name = 'cuda'
    pipe = create_diffusers_pipeline(device_name)
    pipe_img2img = pipe_as_img2img(pipe)

    logging.info('creating handlers')

    req_handlers: List[BotRequestHandler] = [
        DiffuseMeHandler(
            pipe=pipe,
            tag_name="diffuse_me",
        ),
        DiffuseItHandler(
            pipe=pipe_img2img,
            tag_name='diffuse_it'
        ),
        DiffuseGameHandler(
            pipe=pipe,
            tag_name='diffuse_game',
            messages=diffusion_game_messages, # type: ignore
            response_duration_sec=60 * 30
        )
    ] # type: ignore

    logging.info('creating listener')
    listener = AppStreamListener(mastodon, pipe,
                                 mention_to_url=my_url,
                                 req_handlers=req_handlers,
                                 toot_listen_start=toot_listen_start,
                                 toot_listen_start_cw=toot_listen_start_cw,
                                 toot_listen_end=toot_listen_end,
                                 device=device_name,
                                 proc_kwargs=proc_kwargs,
                                 **app_stream_listener_kwargs
                                 )

    mastodon.stream_user(listener, run_async=False, timeout=10000)


if __name__ == '__main__':
    main()
