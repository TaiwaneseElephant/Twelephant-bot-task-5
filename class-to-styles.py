import re, json, pywikibot

def ClassToStyles(element, table):
    classtext = re.search(r'class\s*=\s"([^"=]+?)"', element)
    if classtext is None:
        return
    stylestext = re.search(r'style\s*=\s"([^"=]+?)"', element)
    if sylestext is None:
        return
    classes = set(classtext.group(1).split())
    styles = {style[0].strip() : style[1].strip() for style in \
    (style.split(":", 1) for style in stylestext.group(1).split(";"))}
    targetclassea = set(table.keys())
    for classname in (classes & targetclasses):
        stylestable = table[classname]
        for key, value in stylestable:
            if styles.has_key(key):
                continue
            styles[key] = value
    classes = classes - targetclasses
    newclasstext = " ".join(classes)
    newstylestext = "; ".join(style)
    return ChangeClass(ChangeStyles(element, newstylestext), newclasstext)

def ChangeClass(element, classtext):
    return re.sub(r'(?<=class)\s*=\s*"[^"=]+?"', classtext, element)

def ChangeStyles(element, stylestext):
    return re.sub(r'(?<=style)\s*=\s*"[^"=]+?"', stylestext, element)
