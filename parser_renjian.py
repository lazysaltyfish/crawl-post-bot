import re
def parser_func(content):
    REGEX = "url:\\\"(.*?)\\\"[\\s\\S]*?desc:\\\"(.*?)\\\"[\\s\\S]*?title:\"(.*?)\"[\\s\\S]*?ptime:\"(.*?)\""
    def label_lambda(x):
        return {
            "url": x[0],
            "desc": x[1],
            "title": x[2],
            "date": x[3],
        }
    text = content.decode('GBK')
    pattern = re.compile(REGEX, flags=re.MULTILINE)
    res = re.findall(pattern, text)
    label_data = list(map(label_lambda, res))
    return label_data

if __name__ == "__main__":
    print("This is parser of renjian.163.com")
    