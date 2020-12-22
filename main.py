#!/usr/bin/env python3
import argparse
from pathlib import Path
import appdirs
from kellog import info, warning, error, debug
import urllib, urllib.request
import ujson

pkg = "reddit_save_backup"
configPath = Path(appdirs.user_config_dir(pkg))
urlPath = configPath / "urls.json"

# ==================================================================================================
def main(args):
	configPath.mkdir(exist_ok=True)
	savedPaths = list(configPath.glob("saved_*.json"))
	if len(savedPaths) == 0 and not args.url:
		error("Must specify JSON RSS URL with '--url'")
		return
	elif len(savedPaths) > 1:
		users = [p.stem for p in savedPaths]
		error(f"Must specify user with '--user'. Options: {users}")
		return
	elif args.user:
		user = args.user
	else:
		user = urllib.parse.parse_qs(urllib.parse.urlparse(args.url).query)["user"][0] if args.url else savedPaths[0].stem.replace("saved_", "")
		info(f"Using cached user '{user}'")
	savedPath = configPath / f"saved_{user}.json"

	urls = {}
	if urlPath.exists():
		info(f"Loading cached URL for '{user}'")
		with open(urlPath, "r") as file:
			urls = ujson.load(file)
	else:
		with open(urlPath, "w") as file:
			urls.update({user: args.url})
			ujson.dump(urls, file, indent=2, sort_keys=False, ensure_ascii=False, escape_forward_slashes=False, encode_html_chars=False)
	req = urllib.request.Request(urls[user], data=None, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0"})
	info(f"Fetching URL: '{urls[user]}'")
	response = urllib.request.urlopen(req)
	info("Parsing")
	json = ujson.loads(response.read().decode("utf-8"))
	savedNew = {f"https://www.reddit.com{child['data']['permalink']}": child['data'] for child in json["data"]["children"]}
	keysNew = savedNew.keys()

	saved = {}
	if savedPath.exists():
		with open(savedPath, "r") as file:
			saved = ujson.load(file)
	keys = saved.keys()
	keysDiff = keysNew - keys
	info(f"Found {len(keysDiff)} new saved posts")
	if len(keysDiff) >= 1000:
		warning("More than 1000 saved posts, which means you may have rolled over Reddit's limit")
	saved.update(savedNew)
	info(f"Total saved posts: {len(saved)}")
	with open(savedPath, "w") as file:
		ujson.dump(saved, file, indent=2, sort_keys=False, ensure_ascii=False, escape_forward_slashes=False, encode_html_chars=False)
	info(f"Saved to disk: '{savedPath}'")


# ==================================================================================================
def parse_args():
	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument("--url", help="URL of JSON RSS feed")
	parser.add_argument("--user", help="Username in the case of multiple accounts")

	return parser.parse_args()


# ==================================================================================================
if __name__ == "__main__":
	main(parse_args())
