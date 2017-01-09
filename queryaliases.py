import json

def loadAliases():
    #puts saved aliases into an aliases dict
    aliases = {}
    keys = []
    aliasFile = open("aliases.txt").read()
    aliases = json.loads(aliasFile)
    keys = list(aliases.keys())
    return aliases, keys

def saveAliases(aliases):
    #puts an aliases dict into a savefile
    aliasFile = open("aliases.txt", "w")
    aliasFile.write(json.dumps(aliases, indent=4))
    aliasFile.close()

aliases, aliasList = loadAliases()
query = input(": ")
print(aliases[query])
