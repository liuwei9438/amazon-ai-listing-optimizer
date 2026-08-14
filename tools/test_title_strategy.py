from __future__ import annotations

import json
import os

from analyzer.title_strategy_generator import (
    TitleStrategyGenerator,
)


def load_profiles(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)



def main():

    api_key = os.getenv(
        "OPENAI_API_KEY"
    )


    if not api_key:

        raise RuntimeError(
            "Missing OPENAI_API_KEY"
        )


    profiles = load_profiles(
        "product_profiles_v2.4.3.json"
    )


    generator = TitleStrategyGenerator()


    # 测试前3个产品
    for index, profile in enumerate(
        profiles[:3]
    ):

        print(
            "\n===================="
        )

        print(
            f"PRODUCT {index+1}"
        )


        result = (
            generator.generate(
                profile,
                api_key,
            )
        )


        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            )
        )



if __name__ == "__main__":

    main()
