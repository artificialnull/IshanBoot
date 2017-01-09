import json

def loadAliases():
    #puts saved aliases into an aliases dict
    aliases = {}
    keys = []
    aliasFile = open("aliases.txt").read()
    for term in aliasFile.split("</term>\n"):
        term = term.replace("<term>","")
        alias = term.split("=")[0]
        value = "=".join(term.split("=")[1:])
        if alias != "" and value != "":
            aliases[alias] = value
            keys.append(alias)
    return aliases, keys

def saveAliases(aliases):
    #puts an aliases dict into a savefile
    aliasFile = open("aliases.txt", "w")
    aliasFile.write(json.dumps(aliases, indent=4))
    aliasFile.close()

aliases, aliasList = loadAliases()
saveAliases(aliases)
