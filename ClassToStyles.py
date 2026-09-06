import re

def ClassToStyles(element, table):
    classtext = re.search(r'class\s*=\s"([^"=]+?)"', element)
    if classtext is None:
        return
    stylestext = re.search(r'style\s*=\s"([^"=]+?)"', element)
    if sylestext is None:
        return
    classes = classtext.group(1).split()
    styles = {style[0].strip() : style[1].strip() for style in (style.split(":", 1) for style in stylestext.group(1).split(";"))}
    for classname, stylestable in table.items():
        if classname in classes:
            for key, value in stylestable:
                if styles.has_key(key):
                    continue
                styles[key] = value
            classes.remove(classname)
    newclasstext = " ".join(classes)
    newstylestext = "; ".join(style)
    return changeclass(changestyles(element, newstylestext),newclasstext)

def changeclass(element, classtext):
    return re.sub(r'(?<=class)\s*=\s*"[^"=]+?"', classtext, element)

def changestyles(element, stylestext):
    return re.sub(r'(?<=style)\s*=\s*"[^"=]+?"', stylestext, element)
