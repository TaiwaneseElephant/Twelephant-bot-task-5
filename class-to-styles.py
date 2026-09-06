import re, json, pywikibot

def ClassToStyles(element, table):
    classtext = re.search(r'class\s*=\s"([\w\d- ]+?)"', element)
    if classtext is None:
        return
    stylestext = re.search(r'style\s*=\s"([^"=]+?)"', element)
    if sylestext is None:
        return
    classes = set(classtext.group(1).split())
    styles = {style[0].strip() : style[1].strip() for style in (style.split(":", 1) for style in stylestext.group(1).split(";"))}
    targetclasses = set(table.keys())
    for classname in (classes & targetclasses):
        stylestable = table[classname]
        styles = ChangeStyles(neweelement, addstyles, styles = styles, replace = False, returnval = "table")
    return ChangeClass(ChangeStyles(element, styles, styles = styles, replace = False, returnval = "element"), targetclasses, classes = classes)

def ChangeClass(element, addclasses:set, removeclasses:set, classes:set = None):
    if classes is None:
        classtext = re.search(r'class\s*=\s"([\w\d- ]+?)"', element)
        if classtext is None:
            return
    classes = set(classtext.group(1).split()) - removeclasses
    classes.update(addclasses)
    return re.sub(r'(?<=class\s*=\s*")[\w\d- ]+?(?=")', " ".join(classes), element)

def ChangeStyles(element, addstyles:dict = {}, removestyles:iter = [], styles:dict = None, replace:bool = True, returnval:str= "element"):
    if styles is None:
        stylestext = re.search(r'styles\s*=\s"([^"=>\n]+?)"', element)
        if stylestext is None:
            return
        styles = {style[0].strip() : style[1].strip() for style in (style.split(":", 1) for style in stylestext.group(1).split(";"))}
    for style in removestyles:
        if styles.has_key(key):
            del styles[style]
    for key, value in addstyles:
        if not replace or styles.has_key(key):
            continue
        styles[key] = value
    if returnval == "element":
        return re.sub(r'(?<=style\s*=\s*")[^"=>\n]+?(?=")', "; ".join(styles), element)
    elif returnval == "table":
        return styles
    else:
        raise ValueError(f"Unexpected value for 'returnval': {returnval}")
