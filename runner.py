from interpreterv3 import Interpreter


inputfile = "test1.src"
with open(inputfile) as handle:
    input = list(map(lambda x:x.rstrip('\n'), handle.readlines()))
i = Interpreter()
i.run(input)

