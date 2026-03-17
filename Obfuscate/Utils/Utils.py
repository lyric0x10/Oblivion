import random
import string

class Utils():
    def FindAllInstances(self, Dict, Key, Target):
        def SearchNode(Tree, Key, Target, CurrentPath=None):
            if CurrentPath is None:
                CurrentPath = []

            Blocks = []

            if type(Tree) == dict:
                Keys = Tree.keys()
                if Key in Keys:
                    if Tree[Key] == Target:
                        Blocks.append(CurrentPath.copy() + [Key])

                for k in Keys:
                    _Block = Tree[k]
                    new_path = CurrentPath + [k]
                    Blocks.extend(SearchNode(_Block, Key, Target, new_path))

            elif type(Tree) == list:
                for i, item in enumerate(Tree):
                    new_path = CurrentPath + [i]
                    Blocks.extend(SearchNode(item, Key, Target, new_path))

            return Blocks

        _ = SearchNode(Dict, Key, Target)
        return _

    def DuplicateFinder(self, List):
        Seen = set()
        Duplicates = []
        for i, item in enumerate(List):
            if item in Seen:
                Duplicates.append(i)
            else:
                Seen.add(item)
        return list(Duplicates)

    def RandomString(self, Length):
        Characters = string.ascii_letters + string.digits
        Result = ''.join(random.choice(Characters) for _ in range(Length))
        if Result[0] in string.digits:
            Result = random.choice(string.ascii_letters) + Result[1:]
        return Result