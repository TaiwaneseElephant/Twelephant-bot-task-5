import re, json, pywikibot
from pywikibot import textlib, pagegenerators

def save(site, page, func = lambda x:x, summary:str = "", max_retry_times:int = 3, **kargs) -> bool:
    e = None
    if page.exists():
        oringinal_text = page.get(force = True, get_redirect = False)
    else:
      return False
    for _ in range(max_retry_times):
        try:
            page.text = func(oringinal_text, **kargs)
            page.save(summary, minor = True, bot=True)
            return True
        except pywikibot.exceptions.EditConflictError as e:
            print(f"Warning! There is an edit conflict on page '{page.title()}'!", flush=True)
            oringinal_text = page.get(force = True, get_redirect = False)
        except pywikibot.exceptions.LockedPageError as e:
            print(f"Warning! The edit attempt on page '{page.title()}' was disallowed because the page is protected!", flush=True)
            break
        except pywikibot.exceptions.AbuseFilterDisallowedError as e:
            print(f"Warning! The edit attempt on page '{page.title()}' was disallowed by the AbuseFilter!", flush=True)
            break
        except pywikibot.exceptions.SpamblacklistError as e:
            print(f"Warning! The edit attempt on page '{page.title()}' was disallowed by the SpamFilter because the edit add blacklisted URL!", flush=True)
            break
        except pywikibot.exceptions.TitleblacklistError as e:
            print(f"Warning! The edit attempt on page '{page.title()}' was disallowed because the title is blacklisted!", flush=True)
            break
    print(f"The attempt to edit the page '{page.title()}' was stopped because of the error below:\n{e}.", flush=True)
    return False

def ClassToStyles(element, table):
    classtext = re.search(r'''class\s*=\s["']([\w\d- ]+?)["']''', element)
    if classtext is None:
        return element
    stylestext = re.search(r'''style\s*=\s["']([^"'=>\n]+?)["']''', element)
    if stylestext is None:
        styles = {}
    else:
        styles = {style[0].strip() : style[1].strip() for style in (style.split(":", 1) for style in stylestext.group(1).split(";"))}
    classes = set(classtext.group(1).split())
    targetclasses = set(table.keys())
    for classname in (classes & targetclasses):
        stylestable = table[classname]
        styles = ChangeStyles(addstyles = stylestable, styles = styles, replace = False, returnval = "table")
    return ChangeClass(ChangeStyles(element, styles, styles = styles, replace = False, returnval = "element"), targetclasses, classes = classes)

def ChangeClass(element, addclasses:set, removeclasses:set, classes:set = None):
    if classes is None:
        classtext = re.search(r'''class\s*=\s*["']([\w\d\- ]+?)["']''', element)
        if classtext is None:
            classes = {}
        else:
            classes = set(classtext.group(1).split())
    classes = classes - removeclasses
    classes.update(addclasses)
    newclasstext = f'class="{" ".join(classes)}"'
    element, num = re.subn(r''''class\s*=\s*["'][\w\d\- ]+?["']''', newclasstext, element)
    if num == 0:
        element += f" {newclasstext}"
    return element

def ChangeStyles(element:str = "", addstyles:dict = {}, removestyles:iter = [], styles:dict = None, replace:bool = True, returnval:str= "element"):
    if styles is None:
        stylestext = re.search(r'''styles\s*=\s*["']([^"'=>\n]+?)["']''', element)
        if stylestext is None:
            styles = {}
        else:
            styles = {style[0].strip() : style[1].strip() for style in (style.split(":", 1) for style in stylestext.group(1).split(";"))}
    for style in removestyles:
        if style in styles.keys():
            del styles[style]
    for key, value in addstyles.items():
        if not replace or (key in styles.keys()):
            continue
        styles[key] = value
    if returnval == "element":
        newstylestext = f'style="{"; ".join([f"{key}:{value}" for key, value in styles.items()])}"'
        element, num = re.subn(r'''style\s*=\s*["'][^"'=>\n]+?["']''', newstylestext, element)
        if num == 0:
            element += f" {newstylestext}"
        return element
    elif returnval == "table":
        return styles
    else:
        raise ValueError(f"Unexpected value for 'returnval': {returnval}")

def pageprocess(text:str, table:dict):
    newcontent = text
    for match in re.finditer(r"<(div|p|span) ([^>\n]+)>", text):
        newcontent = newcontent.replace(match.group(), f"<{match.group(1)} {ClassToStyles(match.group(2).strip(), table)}>")
    for match in re.finditer(r"(?:^|\n)\s*{| (.*=.*)", text):
        newcontent = newcontent.replace(match.group(), f"{| {ClassToStyles(match.group(1).strip(), table)}")
    return newcontent

def main():
    site = pywikibot.Site("wikipedia:zh")
    try:
        config = json.loads(pywikibot.Page(site, "User:Twelephant-bot/task/5/config.json").text)
        if not config["Enable"]:
            return
        table = config["table"]
        query = config["query"]
        summary = config["summary"]
    except:
        print("Failed to load config.")
        return
    for page in pagegenerators.SearchPageGenerator(query, site=site, content=True):
        save(site, page, pageprocess, summary, table = table)
