import re, json, pywikibot
from pywikibot import textlib, pagegenerators

CLASS_PATTERN = re.compile(r'''class\s*=\s*?["']?((?:[\w\d\- ](?!\=))+)["' ]''')
STYLES_PATTERN = re.compile(r'''style\s*=\s*["']?((?:[^"'=>\n](?!\=))+)["' ]''')

def save(site, page, func = lambda x:x, summary:str = "", max_retry_times:int = 3, **kargs) -> bool:
    e = None
    if page.exists() and page.botMayEdit():
        original_text = page.text
    else:
      return False
    for _ in range(max_retry_times):
        try:
            page.text = func(original_text, **kargs)
            if page.text != original_text:
                page.save(summary, minor = True, bot=True)
                return True
            else:
                print("No difference.")
                return False
        except pywikibot.exceptions.EditConflictError as e:
            print(f"Warning! There is an edit conflict on page '{page.title()}'!", flush=True)
            original_text = page.get(force = True, get_redirect = False)
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
    classtext = CLASS_PATTERN.search(element)
    if classtext is None:
        return element
    stylestext = STYLES_PATTERN.search(element)
    if stylestext is None:
        styles = {}
    else:
        styles = {style[0].strip() : style[1].strip() for style in (style.split(":", 1) for style in stylestext.group(1).split(";")  if ":" in style)}
    classes = set(classtext.group(1).split())
    targetclasses = set(table.keys())
    intersection = classes & targetclasses
    if len(intersection) == 0:
        return element
    for classname in (intersection):
        stylestable = table[classname]
        styles = ChangeStyles(addstyles = stylestable, styles = styles, replace = False, returnval = "table")
    return ChangeClass(ChangeStyles(element, styles = styles, replace = False, returnval = "element"), removeclasses = targetclasses, classes = classes).lstrip()

def ChangeClass(element, addclasses:set = None, removeclasses:set = None, classes:set = None):
    if classes is None:
        classtext = CLASS_PATTERN.search(element)
        if classtext is None:
            classes = set()
        else:
            classes = set(classtext.group(1).split())
    if removeclasses is not None:
        classes = classes - removeclasses
    if addclasses is not None:
        classes.update(addclasses)
    if len(classes) > 0:
        newclasstext = f' class="{" ".join(classes)}"'
    else:
        newclasstext = ""
    element, num = re.subn(r''' *class\s*=\s*["']?((?:[\w\d\- ](?!\=))+)["' ]''', newclasstext, element)
    if num == 0 and len(classes) > 0:
        element += newclasstext
    return element.rstrip()

def ChangeStyles(element:str = "", addstyles:dict = None, removestyles:iter = None, styles:dict = None, replace:bool = True, returnval:str= "element"):
    if styles is None:
        stylestext = STYLES_PATTERN.search(element)
        if stylestext is None:
            styles = {}
        else:
            styles = {style[0].strip() : style[1].strip() for style in (style.split(":", 1) for style in stylestext.group(1).split(";") if ":" in style)}
    if removestyles is not None:
        for style in removestyles:
            if style in styles.keys():
                del styles[style]
    if addstyles is not None:
        for key, value in addstyles.items():
            if not replace and (key in styles.keys()):
                continue
            styles[key] = value
    if returnval == "element":
        if len(styles) > 0:
            newstylestext = f' style="{"; ".join([f"{key}:{value}" for key, value in styles.items()])}"'
        else:
            newstylestext = ""
        element, num = re.subn(r''' *style\s*=\s*["']?((?:[^"'=>\n](?!\=))+)["' ]''', newstylestext, element)
        if num == 0 and len(styles) > 0:
            element += newstylestext
        return element.rstrip()
    elif returnval == "table":
        return styles
    else:
        raise ValueError(f"Unexpected value for 'returnval': {returnval}")

def pageprocess(text:str, table:dict, target_tags:str, ignore_tags:str = None):
    content = text
    if ignore_tags is not None:
        content = content.replace("&#x2060;", "")
        temp = []
        def remove_ignore_tags(match):
            temp.append(match.group())
            return f"&#x2060;{len(temp)}&#x2060;"
        content = re.sub(rf"<({ignore_tags})(?: [^>\n]*)?>[\s\S]+?</\1 *>", remove_ignore_tags, content, flags=re.IGNORECASE)
    content = re.sub(rf"<({target_tags}) +([^>\n]+)>", lambda match : f"<{match.group(1)} {ClassToStyles(match.group(2).strip(), table)}>", content, flags=re.IGNORECASE)
    content = re.sub(r"((?:^|\n)\s*\{\| *)(.*=.*)", lambda match : f"{match.group(1)}{ClassToStyles(match.group(2).strip(), table)}", content, flags=re.IGNORECASE)
    if ignore_tags is not None:
        for i in range(len(temp)):
            content = content.replace(f"&#x2060;{i + 1}&#x2060;", temp[i], 1)
    return content

def check_switch(site) -> bool:
    try:
        switch_page = pwb.Page(site, "User:Twelephant-bot/task/2/config.json")
        return json.loads(switch_page.text)["Enable"]
    except:
        return False

def main():
    site = pywikibot.Site("wikipedia:zh")
    try:
        config = json.loads(pywikibot.Page(site, "User:Twelephant-bot/task/5/config.json").text)
        if not config["Enable"]:
            print("Stop.")
            return
        table = config["table"]
        target_tags = "|".join(config["target tags"])
        ignore_tags = "|".join(config["ignore tags"])
        query = config["query"]
        summary = config["summary"]
    except:
        print("Failed to load config.")
        return
    t = 0
    for page in pagegenerators.SearchPageGenerator(query, site=site, content=True):
        success = save(site, page, pageprocess, summary, table = table, target_tags = target_tags, ignore_tags = ignore_tags)
        if success:
            t += 1
            if t % 10 == 0 and not check_switch(site):
                break
if __name__ == "__main__":
    main()
