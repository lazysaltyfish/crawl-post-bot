import re
import datetime

def parser_func(content):
    REGEX = r"<div class=\"corriente\">[\s\S]*?<a href=\"(.*?)\">\s+(.*?)\s+<small>-\s(.*?)</small>"
    
    def label_lambda(x):
        url, title, author = x

        return {
            "url": url,
            "desc": '',
            "title": title,
            "date": str(datetime.date.today())
        }

    text = content.decode('utf8')
    pattern = re.compile(REGEX, flags=re.MULTILINE)
    res = re.findall(pattern, text)
    label_data = list(map(label_lambda, res))
    return label_data

if __name__ == "__main__":
    print("This is parser of www.guancha.cn")
