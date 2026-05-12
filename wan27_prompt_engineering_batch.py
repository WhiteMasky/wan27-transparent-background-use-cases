import base64
import json
import os
import random
import time
from pathlib import Path
from typing import Any

import dashscope
import requests
from dashscope.aigc.image_generation import ImageGeneration
from dashscope.api_entities.dashscope_response import Message
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "wan27_prompt_engineering_50x2_results"
GEN_DIR = OUT_DIR / "generation"
EDIT_DIR = OUT_DIR / "editing"
REF_DIR = OUT_DIR / "references"
for directory in (OUT_DIR, GEN_DIR, EDIT_DIR, REF_DIR):
    directory.mkdir(exist_ok=True)

dashscope.base_http_api_url = "https://dashscope-intl.aliyuncs.com/api/v1"

GENERATION_TEMPLATE = """
Create a production-ready isolated asset as a real PNG with transparent background.
The background must be fully transparent using the PNG alpha channel.
Do not draw a checkerboard pattern, white canvas, gray canvas, colored backdrop, shadow box, scene, floor, wall, table, border, frame, poster rectangle, texture background, rays, or decorative background.
Subject only, centered, clean cutout edges, natural antialiasing on edge pixels.
This is an output-format constraint, not a visual style.
Use isolated asset, subject only, and catalog cutout behavior.
Keep the same object visually complete, with no cropped edges.
""".strip()

EDITING_TEMPLATE = """
Return a real PNG with transparent background using the PNG alpha channel.
If the input already has transparency, preserve the exact existing alpha mask outside the edited subject.
If the input has an opaque background, remove the original background completely.
Output only the edited subject, centered, clean antialiased cutout edges.
No checkerboard, no white canvas, no gray canvas, no colored backdrop, no wall, no floor, no table, no scene, no frame, no poster rectangle, no decorative background, no texture background, no rays.
For recolor or reshaping, keep the same silhouette, geometry, lighting, texture, and object layout unless the edit explicitly asks to transform it.
For multi-object edits, create a transparent asset cluster with floating decorative elements, not a poster background.
This is an output-format constraint, not a visual style.
""".strip()


GENERATION_CASES = [
    ("gen_001_luxury_perfume", "电商商品", "A luxury perfume bottle with faceted glass, silver cap, pale amber liquid, premium ecommerce product render."),
    ("gen_002_foldable_phone", "电子商品", "A foldable smartphone half open, glossy black frame, vivid screen UI glow contained to the screen."),
    ("gen_003_robot_vacuum", "家电商品", "A modern robot vacuum cleaner with lidar tower, white shell, subtle product lighting."),
    ("gen_004_sushi_platter", "餐饮素材", "A photorealistic sushi platter with salmon, tuna, wasabi, ginger, arranged as menu cutout asset."),
    ("gen_005_iced_coffee", "餐饮素材", "A clear plastic cup of iced coffee with cream swirl and ice cubes, cafe menu product cutout."),
    ("gen_006_birthday_cake", "餐饮素材", "A colorful birthday cake slice with candle, frosting layers, sprinkles, isolated dessert asset."),
    ("gen_007_winter_coat", "服饰", "A long olive green winter parka coat floating front view, realistic fabric and zipper details."),
    ("gen_008_handbag", "服饰", "A structured leather handbag in burgundy, gold hardware, three-quarter catalog view."),
    ("gen_009_sunglasses", "服饰", "A pair of futuristic sunglasses with translucent blue lenses, clean product cutout."),
    ("gen_010_running_outfit", "服饰", "A complete running outfit set: jacket, shorts, socks, cap, and shoes arranged as floating catalog flatlay."),
    ("gen_011_anime_knight", "动漫人物", "A full-body original anime cyber knight character, luminous sword, armor plates, dynamic stance."),
    ("gen_012_anime_idol", "动漫人物", "A full-body original anime idol performer, layered stage outfit, microphone, star accessories."),
    ("gen_013_chibi_doctor", "动漫贴纸", "A chibi doctor character sticker holding a clipboard, friendly expression, white outline around character only."),
    ("gen_014_game_pet", "游戏素材", "A cute fantasy game pet creature with tiny wings, round body, gem collar, collectible asset style."),
    ("gen_015_real_model_streetwear", "真人模特", "A realistic full-body male streetwear model wearing denim jacket, cargo pants, sneakers, confident standing pose."),
    ("gen_016_real_model_beauty", "真人模特", "A realistic half-body beauty model holding a skincare bottle, clean commercial lighting."),
    ("gen_017_real_model_doctor", "真人模特", "A realistic professional doctor portrait, white coat, stethoscope, tablet in hand, website hero cutout."),
    ("gen_018_fitness_trainer", "真人模特", "A realistic fitness trainer holding a kettlebell, athletic apparel, energetic pose."),
    ("gen_019_sale_burst", "海报素材", "A bold sale burst asset with readable English text HOT DEAL, lightning bolts, price tag, sticker shape."),
    ("gen_020_music_title", "海报素材", "A neon music event title asset with readable English text NIGHT BEATS, equalizer bars, chrome ribbon fragments."),
    ("gen_021_spring_campaign", "海报素材", "A spring campaign decorative asset cluster: flowers, coupon shape, ribbon, readable English text SPRING SALE."),
    ("gen_022_app_icon_health", "UI图标", "A polished 3D app icon of a heart and pulse line, red and teal, no text."),
    ("gen_023_app_icon_notes", "UI图标", "A polished 3D app icon of a folded note with spark, blue and yellow, no text."),
    ("gen_024_logo_leaf", "Logo/标识", "A clean vector-style logo mark of a leaf combined with a lightning bolt, green and black, no wordmark."),
    ("gen_025_logo_bakery", "Logo/标识", "A bakery logo badge with readable English text BREAD LAB, wheat icon, warm vector style."),
    ("gen_026_esports_panther", "Logo/标识", "An esports logo mascot of an original panther head, angular red and black vector-like shapes."),
    ("gen_027_cosmetics_set", "商品组合", "A luxury cosmetics set with serum bottle, cream jar, lipstick, botanical accents, clean beauty render."),
    ("gen_028_toolkit", "商品组合", "A home repair toolkit set with drill, measuring tape, screwdriver, wrench, organized floating composition."),
    ("gen_029_camping_gear", "商品组合", "Camping gear bundle: backpack, lantern, mug, compact tent, compass, floating outdoor product kit."),
    ("gen_030_baby_stroller", "商品", "A modern baby stroller in soft gray fabric, side three-quarter ecommerce product render."),
    ("gen_031_bicycle", "商品", "A sleek electric bicycle side view, matte charcoal frame, battery pack visible, product cutout."),
    ("gen_032_watch_bundle", "商品组合", "A premium watch bundle with watch, extra strap, box, polishing cloth, floating arrangement."),
    ("gen_033_kitchen_mixer", "家电商品", "A red stand mixer with stainless bowl, whisk attachment, clean kitchen appliance cutout."),
    ("gen_034_pet_food_pack", "包装商品", "A premium pet food bag package with bowl of kibble and small ingredient pieces, no brand text."),
    ("gen_035_book_stack", "出版素材", "A stack of three hardcover books with bookmarks and reading glasses, editorial cutout asset."),
    ("gen_036_medical_device", "医疗商品", "A portable digital blood pressure monitor with cuff and display, clean medical product render."),
    ("gen_037_education_badge", "教育素材", "An education badge asset with readable English text LEARN FAST, pencil, stars, graduation cap."),
    ("gen_038_travel_pack", "旅游素材", "A travel asset cluster with passport, suitcase, boarding pass, camera, tiny map pins."),
    ("gen_039_real_estate_key", "地产素材", "A real estate key handover asset: gold key, small house model, ribbon, clean commercial render."),
    ("gen_040_finance_coin", "金融素材", "A fintech asset cluster with coins, credit card, upward arrow, secure shield, polished 3D style."),
    ("gen_041_car_part", "汽车配件", "A sport car alloy wheel rim with tire, metallic reflections, product catalog cutout."),
    ("gen_042_motorcycle_helmet", "商品", "A motorcycle helmet with glossy black shell and red visor, three-quarter render."),
    ("gen_043_flower_bouquet", "花艺素材", "A wedding flower bouquet with white roses, eucalyptus, silk ribbon, isolated floral asset."),
    ("gen_044_toy_robot", "玩具商品", "A colorful toy robot with movable arms, friendly face, plastic product render."),
    ("gen_045_board_game", "玩具商品", "A board game product set with box, dice, cards, tokens arranged as floating ecommerce asset."),
    ("gen_046_burger_combo", "餐饮素材", "A burger combo with burger, fries, soda, sauce cup, appetizing food delivery cutout."),
    ("gen_047_cocktail", "餐饮素材", "A tropical cocktail glass with fruit garnish, condensation, colorful drink menu cutout."),
    ("gen_048_furniture_chair", "家具商品", "A modern lounge chair with wooden legs and boucle fabric, catalog product cutout."),
    ("gen_049_lamp", "家具商品", "A sculptural table lamp with brass base and frosted glass shade, product render."),
    ("gen_050_packaging_box", "包装商品", "A premium subscription box with tissue paper, product inserts, small sample bottles, unbranded packaging."),
]


REFERENCE_SOURCES = {
    "tshirt": "https://loremflickr.com/1024/768/tshirt",
    "shoes": "https://loremflickr.com/1024/768/shoes",
    "ramen": "https://loremflickr.com/1024/768/ramen",
    "watch": "https://loremflickr.com/1024/768/watch",
    "car": "https://loremflickr.com/1024/768/car",
    "burger": "https://loremflickr.com/1024/768/burger",
    "cosmetics": "https://loremflickr.com/1024/768/cosmetics",
    "keyboard": "https://loremflickr.com/1024/768/keyboard",
    "bag": "https://loremflickr.com/1024/768/handbag",
    "chair": "https://loremflickr.com/1024/768/chair",
    "transparent_rocket": "https://raw.githubusercontent.com/hfg-gmuend/openmoji/master/color/618x618/1F680.png",
    "transparent_tshirt": "https://raw.githubusercontent.com/hfg-gmuend/openmoji/master/color/618x618/1F455.png",
    "transparent_lightbulb": "https://raw.githubusercontent.com/hfg-gmuend/openmoji/master/color/618x618/1F4A1.png",
    "transparent_star": "https://raw.githubusercontent.com/hfg-gmuend/openmoji/master/color/618x618/2B50.png",
    "transparent_python": "https://raw.githubusercontent.com/github/explore/main/topics/python/python.png",
    "local_sneakers": str(ROOT / "transparent_bg_complex21_results" / "clothing_sneaker_pair_wan2-7-image-pro.png"),
    "local_model": str(ROOT / "transparent_bg_complex21_results" / "real_model_business_portrait_wan2-7-image-pro.png"),
    "local_cosmetics": str(ROOT / "transparent_bg_complex21_results" / "product_cosmetics_collection_wan2-7-image-pro.png"),
}


EDIT_CASES = [
    ("edit_001_tshirt_blue_cutout", "服饰抠图换色", ["tshirt"], "Edit Image 1: isolate the shirt/person apparel subject as a clean ecommerce cutout and recolor the main T-shirt fabric to cobalt blue."),
    ("edit_002_shoes_black_orange", "鞋类抠图换色", ["shoes"], "Edit Image 1: remove the entire photo background, keep only the shoes, recolor uppers to matte black and soles to bright orange."),
    ("edit_003_ramen_add_egg", "餐饮抠图加料", ["ramen"], "Edit Image 1: isolate the ramen bowl and add one halved soft-boiled egg plus fresh green onions on top."),
    ("edit_004_watch_red_strap", "电子商品改色", ["watch"], "Edit Image 1: isolate the watch and change the strap to deep red silicone while preserving the watch face."),
    ("edit_005_car_teal", "汽车抠图改色", ["car"], "Edit Image 1: isolate the car and change body paint to metallic teal, preserving windows, wheels, and lighting."),
    ("edit_006_burger_menu_cutout", "餐饮抠图", ["burger"], "Edit Image 1: isolate the burger or food item as a delivery menu cutout and make it look more appetizing with warmer highlights."),
    ("edit_007_cosmetics_black_gold", "商品包装改色", ["cosmetics"], "Edit Image 1: isolate the cosmetics products and change packaging to matte black with gold label accents."),
    ("edit_008_keyboard_rgb", "电子商品改色", ["keyboard"], "Edit Image 1: isolate the keyboard and add subtle RGB lighting to the keys without creating a desk or room."),
    ("edit_009_bag_pastel", "包袋改色", ["bag"], "Edit Image 1: isolate the handbag and recolor it to pastel lavender leather with silver hardware."),
    ("edit_010_chair_green", "家具改色", ["chair"], "Edit Image 1: isolate the chair and recolor upholstery to forest green velvet while keeping legs unchanged."),
    ("edit_011_rocket_3d", "透明图标变形", ["transparent_rocket"], "Edit Image 1: preserve transparency and morph the rocket icon into a glossy 3D sticker with a thick clean outline."),
    ("edit_012_tshirt_lightning", "透明图标加图案", ["transparent_tshirt"], "Edit Image 1: preserve transparency and add a yellow lightning bolt print centered on the shirt."),
    ("edit_013_lightbulb_neon", "透明图标改风格", ["transparent_lightbulb"], "Edit Image 1: preserve transparency and turn the bulb into a neon glass app icon with cyan glow contained to the object."),
    ("edit_014_star_gold", "透明图标质感", ["transparent_star"], "Edit Image 1: preserve transparency and turn the star into a polished metallic gold sticker asset."),
    ("edit_015_python_badge", "透明Logo质感", ["transparent_python"], "Edit Image 1: preserve transparency and transform the Python logo into a raised enamel badge with subtle bevel."),
    ("edit_016_local_sneakers_hightop", "透明商品变形", ["local_sneakers"], "Edit Image 1: preserve transparent background and transform the sneakers into high-top basketball shoes with thicker ankle collars."),
    ("edit_017_local_model_hoodie", "透明真人换装", ["local_model"], "Edit Image 1: preserve transparent background and change the blazer into a red casual hoodie while keeping pose and tablet."),
    ("edit_018_local_cosmetics_refill", "透明商品改包装", ["local_cosmetics"], "Edit Image 1: preserve transparent background and change all packaging to refillable glass bottles with green labels."),
    ("edit_019_ramen_rocket_cluster", "多图拼接", ["ramen", "transparent_rocket"], "Use Image 1 as the food subject and Image 2 as decorative reference. Create a transparent food poster asset cluster with small rocket stickers floating around the ramen."),
    ("edit_020_tshirt_python_print", "多图服装合成", ["tshirt", "transparent_python"], "Use Image 1 as apparel reference and Image 2 as the print. Remove the background and place the logo centered on the shirt."),
    ("edit_021_car_star_decal", "多图贴花合成", ["car", "transparent_star"], "Use Image 1 as the car and Image 2 as decal reference. Isolate the car and add a small gold star decal on the door."),
    ("edit_022_bag_lightbulb_charm", "多图配件合成", ["bag", "transparent_lightbulb"], "Use Image 1 as the handbag and Image 2 as charm reference. Isolate the bag and add a small lightbulb keychain charm."),
    ("edit_023_watch_star_face", "局部替换", ["watch", "transparent_star"], "Use Image 2 as design reference. Isolate the watch and put a small gold star symbol on the watch face."),
    ("edit_024_keyboard_remove_cable", "删元素", ["keyboard"], "Edit Image 1: isolate the keyboard and remove any visible cable, keeping the keyboard complete and clean."),
    ("edit_025_cosmetics_remove_lipstick", "删元素", ["cosmetics"], "Edit Image 1: isolate the cosmetics collection and remove the lipstick item, closing the composition naturally."),
    ("edit_026_shoes_blue_laces", "局部改色", ["shoes"], "Edit Image 1: isolate the shoes and change only the laces to bright electric blue."),
    ("edit_027_tshirt_add_pocket", "服饰变形", ["tshirt"], "Edit Image 1: isolate the T-shirt apparel subject and add a small chest pocket while preserving garment fabric."),
    ("edit_028_chair_add_pillow", "家具加物", ["chair"], "Edit Image 1: isolate the chair and add a small cream throw pillow on the seat."),
    ("edit_029_burger_add_label", "餐饮促销素材", ["burger"], "Edit Image 1: isolate the food and add a small readable sticker label that says FRESH near the food, still transparent."),
    ("edit_030_ramen_spicy_badge", "餐饮促销素材", ["ramen", "transparent_star"], "Use Image 1 as the ramen and Image 2 as decorative reference. Add a small spicy badge and star accents around the isolated bowl."),
    ("edit_031_car_convertible", "汽车变形", ["car"], "Edit Image 1: isolate the car and subtly transform it into a convertible version while preserving perspective."),
    ("edit_032_watch_gold_case", "电子商品材质", ["watch"], "Edit Image 1: isolate the watch and change the metal case to brushed gold while keeping strap color."),
    ("edit_033_bag_monogram", "包袋图案", ["bag"], "Edit Image 1: isolate the handbag and add a subtle repeating monogram pattern with no readable letters."),
    ("edit_034_cosmetics_add_leaf", "商品加元素", ["cosmetics"], "Edit Image 1: isolate the cosmetics products and add two fresh green leaf ingredients beside them."),
    ("edit_035_keyboard_compact", "电子商品变形", ["keyboard"], "Edit Image 1: isolate the keyboard and transform it into a compact 75 percent layout while keeping key style."),
    ("edit_036_rocket_smoke", "透明图标加元素", ["transparent_rocket"], "Edit Image 1: preserve transparency and add a small stylized smoke puff attached to the rocket flame."),
    ("edit_037_tshirt_recolor_red", "透明图标改色", ["transparent_tshirt"], "Edit Image 1: preserve transparency and recolor the T-shirt icon to bright red with white collar."),
    ("edit_038_lightbulb_idea_badge", "透明图标加文字", ["transparent_lightbulb"], "Edit Image 1: preserve transparency and add a small readable IDEA label below the bulb as part of the sticker."),
    ("edit_039_star_smile", "透明图标表情", ["transparent_star"], "Edit Image 1: preserve transparency and add a cute smiling face to the star."),
    ("edit_040_python_gold", "透明Logo改色", ["transparent_python"], "Edit Image 1: preserve transparency and recolor the Python logo to black and metallic gold."),
    ("edit_041_sneakers_neon", "透明商品改色", ["local_sneakers"], "Edit Image 1: preserve transparent background and add neon green accents to the sneakers."),
    ("edit_042_model_tablet_logo", "透明真人合成", ["local_model", "transparent_python"], "Use Image 1 as the model and Image 2 as logo reference. Preserve transparency and place a small logo on the tablet screen."),
    ("edit_043_cosmetics_remove_plants", "透明商品删元素", ["local_cosmetics"], "Edit Image 1: preserve transparent background and remove botanical leaf accents while keeping the products."),
    ("edit_044_burger_combo_expand", "餐饮组合", ["burger"], "Edit Image 1: isolate the burger and add fries plus a small sauce cup as a transparent food combo asset."),
    ("edit_045_ramen_to_takeout", "餐饮变形", ["ramen"], "Edit Image 1: isolate the ramen and transform the bowl into a black takeout bowl with chopsticks on top."),
    ("edit_046_car_sport_stripes", "汽车贴花", ["car"], "Edit Image 1: isolate the car and add two white racing stripes along the body."),
    ("edit_047_watch_fitness_ui", "电子商品换屏", ["watch"], "Edit Image 1: isolate the watch and change the face to a fitness tracking UI with heart and steps icons."),
    ("edit_048_chair_rotate_angle", "商品重构", ["chair"], "Edit Image 1: isolate the chair and present it in a cleaner three-quarter product angle."),
    ("edit_049_bag_add_scarf", "配饰加物", ["bag"], "Edit Image 1: isolate the handbag and tie a small silk scarf to one handle."),
    ("edit_050_shoes_make_sandal", "鞋类变形", ["shoes"], "Edit Image 1: isolate the shoes and transform them into sporty sandals while preserving the product-photo realism."),
]


def download_ref(key: str) -> Path:
    source = REFERENCE_SOURCES[key]
    src_path = Path(source)
    if src_path.exists():
        return src_path
    suffix = ".png" if ".png" in source.lower() else ".jpg"
    path = REF_DIR / f"{key}{suffix}"
    if path.exists() and path.stat().st_size > 0:
        return path
    response = requests.get(source, timeout=120, headers={"User-Agent": "Codex Wan2.7 transparent test"})
    response.raise_for_status()
    path.write_bytes(response.content)
    return path


def data_url(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def as_dict(response: Any) -> dict:
    if isinstance(response, dict):
        return response
    try:
        return dict(response)
    except Exception:
        try:
            return response.to_dict()
        except Exception:
            return json.loads(json.dumps(response, default=lambda o: getattr(o, "__dict__", str(o))))


def redact(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: redact(v) for k, v in data.items()}
    if isinstance(data, list):
        return [redact(v) for v in data]
    if isinstance(data, str) and "Expires=" in data:
        return data.split("?")[0] + "?Expires=<redacted>"
    return data


def extract_urls(data: dict) -> list[str]:
    urls = []
    output = data.get("output", {}) or {}
    for item in output.get("results", []) or []:
        if isinstance(item, dict):
            if item.get("url"):
                urls.append(item["url"])
            if item.get("image"):
                urls.append(item["image"])
    for choice in output.get("choices", []) or []:
        for item in choice.get("message", {}).get("content", []) or []:
            if isinstance(item, dict) and item.get("image"):
                urls.append(item["image"])
    return urls


def analyze_image(path: Path) -> dict:
    with Image.open(path) as image:
        converted = image.convert("RGBA")
        alpha = converted.getchannel("A")
        values = list(alpha.getdata())
        total = len(values)
        transparent = sum(1 for v in values if v == 0)
        translucent = sum(1 for v in values if 0 < v < 255)
        non_opaque = transparent + translucent
        bbox = alpha.getbbox()
        preview_path = path.with_name(path.stem + "_checker_preview.jpg")
        checker = Image.new("RGBA", converted.size, (255, 255, 255, 255))
        pixels = checker.load()
        tile = 24
        for y in range(converted.height):
            for x in range(converted.width):
                if ((x // tile) + (y // tile)) % 2:
                    pixels[x, y] = (210, 210, 210, 255)
        Image.alpha_composite(checker, converted).convert("RGB").save(preview_path, quality=90)
        return {
            "format": image.format,
            "mode": image.mode,
            "size": list(image.size),
            "has_alpha_mode": image.mode in ("RGBA", "LA") or "transparency" in image.info,
            "transparent_pixel_ratio": transparent / total,
            "translucent_pixel_ratio": translucent / total,
            "non_opaque_pixel_ratio": non_opaque / total,
            "alpha_bbox": list(bbox) if bbox else None,
            "alpha_success": image.mode in ("RGBA", "LA") and transparent / total > 0.01,
            "preview": str(preview_path),
        }


def call_wan(api_key: str, content: list[dict]) -> dict:
    message = Message(role="user", content=content)
    response = ImageGeneration.async_call(
        api_key=api_key,
        model="wan2.7-image-pro",
        messages=[message],
        n=1,
        size="1K",
        watermark=False,
        enable_sequential=False,
        thinking_mode=True,
    )
    if getattr(response, "status_code", None) == 200:
        response = ImageGeneration.wait(task=response, api_key=api_key)
    return as_dict(response)


def run_generation(api_key: str, case: tuple[str, str, str], index: int) -> dict:
    case_id, category, brief = case
    image_path = GEN_DIR / f"{case_id}.png"
    summary_path = GEN_DIR / f"{case_id}.json"
    if image_path.exists() and summary_path.exists():
        return json.loads(summary_path.read_text(encoding="utf-8"))
    prompt = f"{GENERATION_TEMPLATE}\n\nAsset brief: {brief}"
    result = {"id": case_id, "kind": "generation", "category": category, "prompt": prompt}
    try:
        data = call_wan(api_key, [{"text": prompt}])
        (GEN_DIR / f"{case_id}_response_redacted.json").write_text(json.dumps(redact(data), ensure_ascii=False, indent=2), encoding="utf-8")
        if data.get("status_code") != 200:
            result.update({"alpha_success": False, "error": data})
        else:
            urls = extract_urls(data)
            if not urls:
                result.update({"alpha_success": False, "error": "no image url"})
            else:
                response = requests.get(urls[0], timeout=120)
                response.raise_for_status()
                image_path.write_bytes(response.content)
                result.update({"file": str(image_path), **analyze_image(image_path)})
    except Exception as exc:
        result.update({"alpha_success": False, "error": f"{type(exc).__name__}: {exc}"})
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def run_edit(api_key: str, case: tuple[str, str, list[str], str], index: int) -> dict:
    case_id, category, refs, edit_goal = case
    image_path = EDIT_DIR / f"{case_id}.png"
    summary_path = EDIT_DIR / f"{case_id}.json"
    if image_path.exists() and summary_path.exists():
        return json.loads(summary_path.read_text(encoding="utf-8"))
    prompt = f"{edit_goal}\n\n{EDITING_TEMPLATE}"
    result = {"id": case_id, "kind": "editing", "category": category, "refs": refs, "prompt": prompt}
    try:
        ref_paths = [download_ref(ref) for ref in refs]
        content = [{"image": data_url(path)} for path in ref_paths]
        content.append({"text": prompt})
        result["reference_files"] = [str(path) for path in ref_paths]
        data = call_wan(api_key, content)
        (EDIT_DIR / f"{case_id}_response_redacted.json").write_text(json.dumps(redact(data), ensure_ascii=False, indent=2), encoding="utf-8")
        if data.get("status_code") != 200:
            result.update({"alpha_success": False, "error": data})
        else:
            urls = extract_urls(data)
            if not urls:
                result.update({"alpha_success": False, "error": "no image url"})
            else:
                response = requests.get(urls[0], timeout=120)
                response.raise_for_status()
                image_path.write_bytes(response.content)
                result.update({"file": str(image_path), **analyze_image(image_path)})
    except Exception as exc:
        result.update({"alpha_success": False, "error": f"{type(exc).__name__}: {exc}"})
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def make_contact_sheet(results: list[dict], path: Path, title: str) -> None:
    cols = 5
    thumb_w, thumb_h, label_h = 220, 200, 74
    rows = (len(results) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h) + 44), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 14)
        small = ImageFont.truetype("arial.ttf", 11)
        title_font = ImageFont.truetype("arial.ttf", 22)
    except Exception:
        font = small = title_font = ImageFont.load_default()
    draw.text((12, 10), title, fill=(20, 20, 20), font=title_font)
    for idx, item in enumerate(results):
        x = (idx % cols) * thumb_w
        y = (idx // cols) * (thumb_h + label_h) + 44
        image_file = item.get("preview") or item.get("file")
        if image_file and Path(image_file).exists():
            with Image.open(image_file) as im:
                im = im.convert("RGB")
                im.thumbnail((thumb_w - 12, thumb_h - 12))
                sheet.paste(im, (x + (thumb_w - im.width) // 2, y + (thumb_h - im.height) // 2))
        success = item.get("alpha_success")
        color = (0, 128, 64) if success else (190, 40, 40)
        draw.text((x + 8, y + thumb_h + 6), f"{idx+1:02d} {'PASS' if success else 'FAIL'}", fill=color, font=font)
        label = item["id"][:26] + ("..." if len(item["id"]) > 26 else "")
        draw.text((x + 8, y + thumb_h + 26), label, fill=(40, 40, 40), font=small)
        ratio = item.get("transparent_pixel_ratio")
        ratio_text = f"transparent={ratio:.1%}" if isinstance(ratio, (int, float)) else "transparent=N/A"
        draw.text((x + 8, y + thumb_h + 46), ratio_text, fill=(40, 40, 40), font=small)
    sheet.save(path, quality=90)


def summarize(results: list[dict]) -> dict:
    return {
        "total": len(results),
        "alpha_success_count": sum(1 for item in results if item.get("alpha_success")),
        "alpha_success_rate": sum(1 for item in results if item.get("alpha_success")) / len(results) if results else 0,
        "results": results,
    }


def main() -> int:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise SystemExit("Set DASHSCOPE_API_KEY")
    random.seed(7)
    generation_results = []
    editing_results = []
    for index, case in enumerate(GENERATION_CASES, start=1):
        print(f"[generation {index}/50] {case[0]}", flush=True)
        generation_results.append(run_generation(api_key, case, index))
        time.sleep(3)
    for index, case in enumerate(EDIT_CASES, start=1):
        print(f"[editing {index}/50] {case[0]}", flush=True)
        editing_results.append(run_edit(api_key, case, index))
        time.sleep(3)
    gen_summary = summarize(generation_results)
    edit_summary = summarize(editing_results)
    overall = {
        "model": "wan2.7-image-pro",
        "generated_at": "2026-05-12",
        "generation": gen_summary,
        "editing": edit_summary,
        "overall": summarize(generation_results + editing_results),
    }
    make_contact_sheet(generation_results, OUT_DIR / "generation_contact_sheet.jpg", "Wan2.7 generation prompts with transparent-background engineering")
    make_contact_sheet(editing_results, OUT_DIR / "editing_contact_sheet.jpg", "Wan2.7 editing prompts with transparent-background engineering")
    (OUT_DIR / "summary.json").write_text(json.dumps(overall, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "generation": {k: gen_summary[k] for k in ("total", "alpha_success_count", "alpha_success_rate")},
        "editing": {k: edit_summary[k] for k in ("total", "alpha_success_count", "alpha_success_rate")},
        "summary": str(OUT_DIR / "summary.json"),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
