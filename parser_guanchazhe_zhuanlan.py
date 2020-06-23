import re
def parser_func(content):
    REGEX = r"<h4 class=\"module-title\"><a href=\"(.*?)\" title=\"(.*?)\"[\s\S]*?<p class=\"module-artile\">(.*?)<a href="
    ROOT_URL = r"https://www.guancha.cn"
    
    def get_datestr_from_url(url):
        filename = url.split(r"/")[-1]
        year, month, day, _ = filename.split("_")
        return "-".join([year, month, day])
    
    def label_lambda(x):
        url_suffix, title, desc = x

        return {
            "url": ROOT_URL + url_suffix,
            "desc": desc,
            "title": title,
            "date": get_datestr_from_url(url_suffix),
        }

    text = content.decode('utf8')
    pattern = re.compile(REGEX, flags=re.MULTILINE)
    res = re.findall(pattern, text)
    label_data = list(map(label_lambda, res))
    return label_data

if __name__ == "__main__":
    print("This is parser of www.guancha.cn")
