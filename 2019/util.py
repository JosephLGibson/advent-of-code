from functools import partial


class Day:
    def __init__(self, day: int, part: int):
        from problems import description

        self.day = day
        self.part = part
        self.desc = description(day, part)
        self.task = self.desc.strip().split("\n")[-1].strip()
        self.data = []
        self.memory = {}

        self.pointer = 0
        self.rel_base = 0
        self.exec_time = -1
        self.debug = False
        self.concurrent = False
        self.input_queue = []

    def __repr__(self):
        return f"Day({self.day,self.part}): Pointer:{self.pointer}"

    def __str__(self):
        return f"Advent of Code class for Day {self.day}: Part {self.part}."

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        import copy

        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, copy.deepcopy(v, memo))
        return result

    def __len__(self):
        return len(self.data)

    def __getitem__(self, position):
        return self.data[position]

    def __eq__(self, other):
        if type(other) == type(self):
            return self.data == other.data
        else:
            return self.data == other

    def __add__(self, other):
        if isinstance(other, list):
            self.data.extend(other)
        else:
            self.data.append(other)
        return self.data

    def __call__(self):
        print(self)
        print(self.desc)
        try:
            self.hist()
        except AttributeError:
            pass
        try:
            self.answer(v=1)
        except AttributeError:
            pass

    def copy(self, deep=False):
        import copy

        if deep is True:
            return copy.deepcopy(self)
        return copy.copy(self)

    def load(self, data=None, typing=str, sep="\n", path="") -> list:
        """Loads Data for Problem
        File _must_ be named dayXX.txt
        Returns data and makes it available as attribte "data"

        Keyword Arguments:
            data {list} -- Load computed data not from file (default: {None})
            typing {type} -- Type of data in list (default: {str})
            sep {str} -- Separator in input data (default: {"\n"})

        Returns:
            list -- Data for Problem
        """
        if path == "":
            path = f"data/day{self.day:02d}.txt"
        if data:
            self.data = data
        else:
            with open(path) as f:
                data = f.read().strip().split(sep)
            self.data = list(map(typing, data))
        self.raw_data = [self.data.copy()]
        self.mem_load()
        return self

    def bake(self):
        """Finalize processed data as resettable
        """
        self.raw_data.append(self.data.copy())
        return self

    def mem_load(self):
        """Loads data into opcode memory
        """
        self.memory = {i: el for i, el in enumerate(self.data)}
        return self

    def mem_dump(self, extend=False):
        """Dumps opcode memory into data

        Keyword Arguments:
            extend {bool} -- Extend data by maximum memory (default: {False})
        """
        for k, v in self.memory.items():
            if k > len(self.data):
                if extend is True:
                    self.data.extend([0] * (k - len(self.data) + 2))
                else:
                    continue
            self.data[k] = v
        return self

    def input(self, data):
        """Input data to queue
        """
        self.input_queue.append(data)
        return self

    def reset(self, hist_step=None):
        """Reset Opcode class

        Resets data, and pointer.
        Flushes input queue.

        Can restore specific data from history

        Keyword Arguments:
            hist_step {[int]} -- restoration point (default: {Last})
        """
        self.pointer = 0
        self.rel_base = 0
        self.input_queue = []
        self.memory = {}

        if hist_step is None:
            hist_step = len(self.raw_data) - 1
        self.data = self.raw_data[hist_step].copy()
        self.raw_data = [x.copy() for x in self.raw_data[: hist_step + 1]]
        self.mem_load()
        return self

    def sum(self) -> float:
        return sum(self.data)

    def apply(self, func, *args, **kwargs) -> list:
        """Apply a function to every element.
        Changes the original data.

        Arguments:
            func {function} -- Function to apply to every element in input

        Returns:
            list -- Function applied to every element in input
        """
        mapfunc = partial(func, *args, **kwargs)
        self.data = list(map(mapfunc, self.data))
        self.mem_load()
        return self

    def time(self):
        from time import time

        if self.exec_time == -1:
            self.exec_time = time()
        else:
            print(f"Execution time was {time()-self.exec_time:.2f} seconds.")
            self.exec_time = -1
        return self

    def execute_opcode(self, reset_pointer=True) -> list:
        """Execute OpCode operation

        1:  Add
        2:  Multiply
        3:  Input
        4:  Output
        5:  Jump If True
        6:  Jump If False
        7:  Less Than
        8:  Equals
        9:  Rel Base Update
        99: Exit

        Returns:
            list -- Opcode after execution
        """

        if reset_pointer is True:
            self.pointer = 0

        def __opmode(pointer: int, mode: tuple, offset: int, get=False) -> int:
            exec_mode = int(mode[offset - 1])
            if exec_mode == 0:
                # Position Mode
                position = self.memory[pointer + offset]
            elif exec_mode == 1:
                # Immediate Mode
                position = pointer + offset
            elif exec_mode == 2:
                # Relative Mode
                position = self.memory[pointer + offset] + self.rel_base
            else:
                raise RuntimeError(f"ERR: \n Exec Mode: {exec_mode} not understood")

            if position < 0:
                raise RuntimeError(
                    f"ERR: \n Memory Access Error: {position} accessed. No Negative Memory Adress!"
                )

            if get:
                return self.memory.get(position, 0)
            else:
                return position

        def __pointer_move(instruction: int):
            step_size = {
                1: 4,
                2: 4,
                3: 2,
                4: 2,
                5: 3,
                6: 3,
                7: 4,
                8: 4,
                9: 2,
                99: 0,
            }
            self.pointer += step_size[instruction]

        def __instructor(code: int):
            mode = f"{code:05d}"
            out_pointer = self.pointer
            instruct = int(mode[3:])
            __pointer_move(instruct)
            return instruct, (mode[2], mode[1], mode[0]), out_pointer

        while True:
            instruct, param, pointer = __instructor(self.memory[self.pointer])
            if instruct == 1:
                # Multiply
                self.memory[__opmode(pointer, param, offset=3)] = __opmode(
                    pointer, param, offset=1, get=True
                ) + __opmode(pointer, param, offset=2, get=True)
            elif instruct == 2:
                # Add
                self.memory[__opmode(pointer, param, offset=3)] = __opmode(
                    pointer, param, offset=1, get=True
                ) * __opmode(pointer, param, offset=2, get=True)
            elif instruct == 3:
                # Input
                if not getattr(self, "input_queue"):
                    self.memory[__opmode(pointer, param, offset=1)] = int(input("Provide input: "))
                elif isinstance(self.input_queue, int):
                    self.memory[__opmode(pointer, param, offset=1)] = self.input_queue
                elif isinstance(self.input_queue, list):
                    self.memory[__opmode(pointer, param, offset=1)] = int(self.input_queue.pop(0))
            elif instruct == 4:
                # Output
                self.result = self.diagnostic = __opmode(pointer, param, offset=1, get=True)
                if self.debug is True:
                    print(self.diagnostic)
                if self.concurrent is True:
                    return self.diagnostic
            elif instruct == 5:
                # Jump If True
                if __opmode(pointer, param, offset=1, get=True) != 0:
                    self.pointer = __opmode(pointer, param, offset=2, get=True)
            elif instruct == 6:
                # Jump If False
                if __opmode(pointer, param, offset=1, get=True) == 0:
                    self.pointer = __opmode(pointer, param, offset=2, get=True)
            elif instruct == 7:
                # Less Than
                self.memory[__opmode(pointer, param, offset=3)] = int(
                    __opmode(pointer, param, offset=1, get=True)
                    < __opmode(pointer, param, offset=2, get=True)
                )
            elif instruct == 8:
                # Equals
                self.memory[__opmode(pointer, param, offset=3)] = int(
                    __opmode(pointer, param, offset=1, get=True)
                    == __opmode(pointer, param, offset=2, get=True)
                )
            elif instruct == 9:
                # Relative Base Adjust
                self.rel_base += int(__opmode(pointer, param, offset=1, get=True))
            elif instruct == 99:
                self.input_queue = []  # Flush inputs
                #self.mem_dump(extend=True)
                return self
            else:
                raise RuntimeError(
                    f"ERR {instruct}: \n Data Dump: {self.memory[pointer]} Index:{pointer}"
                )
                break

    def hist(self):
        """Produce data history
        """
        length = len(self.raw_data)
        ends = ("y", "ies")
        print(f"{length} histor{ends[length != 1]} saved")
        print("=" * 15)
        for hist in self.raw_data:
            s = f"{hist}"
            print(s[:70] + " . . ." * (70 < len(s)))

    def summary(self):
        """Produce Task Summary
        """
        s = f"The problem for Day {self.day} and part {self.part}:\n{self.task}"
        if hasattr(self, "result"):
            print(s)
            self.answer(v=True)
        else:
            print(s)

    def answer(self, num=None, v=False) -> str:
        """Produce answer string

        Saves number in result attribute and returns a nice string

        Keyword Arguments:
            num {int} -- Input result (default: {None})
            v {bool} -- Verbesity (default: {False})

        Returns:
            str -- Answer string
        """
        if num is not None:
            self.result = num
        s = f"The Solution on Day {self.day} for Part {self.part} is: {self.result}"
        if v:
            print(s)
        return s

class Robot(Day):
    def __init__(self, day, part):
        super().__init__(day, part)
        self.concurrent = True
        self.location = (0, 0)
        self.path = {self.location: 0}
        self.direction = 0
        self.painted = set()

    def parse_direction(self):
        dir_dict = {0: (0,  1), # Up
                    1: (1,  0), # Right
                    2: (0, -1), # Down
                    3: (-1, 0)} # Left
        return dir_dict[self.direction]

    def turn(self, direction):
        # left  0 right 1 
        if direction == 0:
            self.direction = (self.direction - 1) % 4
        elif direction == 1:
            self.direction = (self.direction + 1) % 4
        return self.walk()
    
    def walk(self):
        step_x, step_y = self.parse_direction()
        self.location = self.location[0] + step_x, self.location[1] + step_y
        self.path[self.location] = self.path.get(self.location, 0)
        return self

    def vision(self):
        self.input(self.path[self.location])
        return self
    
    def paint(self, color):
        self.path[self.location] = color
        self.painted.add(self.location)
        # black 0 white 1
        return self
    
    def run(self):
        while True:
            # First See
            self.vision()
            # Then think and pause
            out = self.execute_opcode(reset_pointer=False)
            if isinstance(out, Robot):
                break
            # Then paint
            self.paint(out)
            # Then think and pause
            out = self.execute_opcode(reset_pointer=False)
            # Then turn
            self.turn(out)
        return self
    
    def visualize(self):
        x, y = zip(*self.path.keys())
        painting = {0: ".", 1: "#"}
        for j in range(max(y)+1, min(y)-2, -1):
            for i in range(min(x), max(x)+1):
                print(painting[self.path.get((i, j), 0)], end=" ")
            print()
        return self

if __name__ == "__main__":
    day = Day(1, 1)

    day()
