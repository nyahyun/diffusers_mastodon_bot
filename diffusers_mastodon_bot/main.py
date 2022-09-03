from pathlib import Path
from typing import *
import json

from mastodon import Mastodon

import torch

from diffusers import StableDiffusionPipeline

from diffusers_mastodon_bot.app_stream_listener import AppStreamListener


def create_diffusers_pipeline(device_name='cuda'):
    pipe = StableDiffusionPipeline.from_pretrained(
        "CompVis/stable-diffusion-v1-4",
        revision="fp16",
        torch_dtype=torch.float16,
        use_auth_token=True
    )

    pipe = pipe.to(device_name)
    return pipe


def create_diffusers_pipeline_cpu(device_name='cpu'):
    pipe = StableDiffusionPipeline.from_pretrained("CompVis/stable-diffusion-v1-4", use_auth_token=True)

    pipe = pipe.to(device_name)
    return pipe


def read_text_file(filename: str) -> Union[str, None]:
    path = Path(filename)
    if not Path(filename).is_file():
        return None

    content = path.read_text(encoding='utf8').strip()
    if len(content) == 0:
        return None

    return content


def main():
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

    proc_kwargs = read_text_file('./config/proc_kwargs.json')
    if proc_kwargs is not None:
        proc_kwargs = json.loads(proc_kwargs)

    print('starting')
    mastodon = Mastodon(
        access_token=access_token,
        api_base_url=endpoint_url
    )

    print('info checking')
    account = mastodon.account_verify_credentials()
    my_url = account['url']
    my_acct = account['acct']
    print(f'you are, acct: {my_acct} / url: {my_url}')

    print('loading model')
    device_name = 'cuda'
    pipe = create_diffusers_pipeline(device_name)
    # pipe = create_diffusers_pipeline_cpu(device_name)

    print('creating listener')
    listener = AppStreamListener(mastodon, pipe,
                                 mention_to_url=my_url, tag_name='diffuse_me',
                                 toot_listen_start=toot_listen_start,
                                 toot_listen_end=toot_listen_end,
                                 device=device_name,
                                 proc_kwargs=proc_kwargs
                                 )

    mastodon.stream_user(listener, run_async=False, timeout=10000)


if __name__ == '__main__':
    main()
