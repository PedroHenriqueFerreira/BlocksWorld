from tkinter import Tk, Canvas

FONT = ('Arial', 10, 'bold')

BG_COLOR = '#191724'
BLOCK_COLOR = '#2A51BE'

BLOCKS = 0
BLOCK_SIZE = 50
BLOCK_MARGIN = 1

VELOCITY = 2
DELAY = 5

class World:
    def __init__(self, canvas):
        self.canvas = canvas
        self.blocks = {}

    def draw(self, initial_state):
        on_table = [initial for initial in initial_state if 'ontable_' in initial]
        on_block = [initial for initial in initial_state if 'on_' in initial]

        for i, initial in enumerate(on_table):
            name = initial.split('_')[1]

            self.blocks[name] = Block(self, name, i, 0)

        while len(on_block) > 0:
            for initial in on_block[:]:
                name = initial.split('_')[1]
                other = initial.split('_')[2]

                if other not in self.blocks:
                    continue

                x = self.blocks[other].x
                y = self.blocks[other].y + 1

                self.blocks[name] = Block(self, name, x, y)
                on_block.remove(initial)

    def run(self, steps):
        if len(steps) == 0:
            return

        step, *steps = steps
        
        i = int(step.split('_')[0])
                
        delay = 0
        
        name = step.split('_')[2]
        
        if 'unstack' in step:
            delay = self.blocks[name].move_top_timing()
            self.blocks[name].move_top()
            
        elif 'stack' in step:
            other = step.split('_')[3]
            
            delay = self.blocks[name].move_x_timing(self.blocks[other].x)
            self.blocks[name].move_x(self.blocks[other].x)
            
            steps.insert(0, f'{i}_bottom_{name}')

        elif 'pick-up' in step:
            delay = self.blocks[name].move_top_timing()
            self.blocks[name].move_top()

        elif 'put-down' in step:
            x = 0
            
            while self.find_block(x, 0) is not None:
                x += 1
                
            delay = self.blocks[name].move_x_timing(x)
            self.blocks[name].move_x(x)
            
            steps.insert(0, f'{i}_bottom_{name}')
            
        elif 'bottom' in step:
            delay = self.blocks[name].move_bottom_timing()
            self.blocks[name].move_bottom()

        self.canvas.after(delay, self.run, steps)

    def find_block(self, x, y):
        for block in self.blocks:
            if self.blocks[block].x == x and self.blocks[block].y == y:
                return self.blocks[block]

        return None

class Block:
    def __init__(self, world, name, x, y):
        self.x = x
        self.y = y

        self.name = name
        self.world = world

        self.draw()

    @property
    def x0(self):
        return (self.x * 2 + 1) * BLOCK_SIZE

    @property
    def y0(self):
        return ((BLOCKS + 1) - self.y) * BLOCK_SIZE

    @property
    def x1(self):
        return self.x0 + BLOCK_SIZE

    @property
    def y1(self):
        return self.y0 + BLOCK_SIZE

    @property
    def x_middle(self):
        return self.x0 + BLOCK_SIZE / 2

    @property
    def y_middle(self):
        return self.y0 + BLOCK_SIZE / 2

    def draw(self):
        self.rect = self.world.canvas.create_rectangle(
            self.x0,
            self.y0,
            self.x1,
            self.y1,
            width=BLOCK_MARGIN,
            fill=BLOCK_COLOR,
            outline=BG_COLOR
        )

        self.text = self.world.canvas.create_text(
            self.x_middle,
            self.y_middle,
            text=self.name,
            font=FONT,
            fill=BG_COLOR
        )

    def move(self, x, y):
        x0 = self.x0
        y0 = self.y0

        x0_middle = self.x_middle
        y0_middle = self.y_middle

        self.x = x
        self.y = y

        self.move_element(self.rect, x0, y0, self.x0, self.y0)
        self.move_element(self.text, x0_middle, y0_middle, self.x_middle, self.y_middle)

    def move_element(self, element, x0, y0, x1, y1):
        if x0 == x1 and y0 == y1:
            return

        x_velocity = 0
        y_velocity = 0

        if x0 < x1:
            x_velocity = VELOCITY
        elif x0 > x1:
            x_velocity = -VELOCITY

        if y0 < y1:
            y_velocity = VELOCITY
        elif y0 > y1:
            y_velocity = -VELOCITY

        self.world.canvas.move(element, x_velocity, y_velocity)

        self.world.canvas.after(
            DELAY,
            self.move_element,
            element,
            x0 + x_velocity,
            y0 + y_velocity,
            x1,
            y1
        )

    def move_top(self):
        self.move(self.x, BLOCKS + 1)
        
    def move_top_timing(self):
        y = BLOCKS + 1
        return (abs(self.y - y) * BLOCK_SIZE // VELOCITY) * DELAY
        
    def move_bottom(self):
        y = 0
        
        while self.world.find_block(self.x, y) is not None:
            y += 1
        
        self.move(self.x, y)

    def move_bottom_timing(self):
        y = 0
        
        while self.world.find_block(self.x, y) is not None:
            y += 1
        
        return (abs(self.y - y) * BLOCK_SIZE // VELOCITY) * DELAY

    def move_x(self, x):
        self.move(x, self.y)
        
    def move_x_timing(self, x):
        return (abs(self.x - x) * BLOCK_SIZE // VELOCITY) * DELAY

def display(instance, initial_state, steps):
    global BLOCKS
    
    BLOCKS = int(instance.split('-')[1])
    
    WINDOW_WIDTH = (2 * BLOCKS + 1) * BLOCK_SIZE
    WINDOW_HEIGHT = (BLOCKS + 2) * BLOCK_SIZE

    root = Tk()

    canvas = Canvas(root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg=BG_COLOR)

    world = World(canvas)

    world.draw(initial_state)

    world.run(steps)

    canvas.pack(expand=1)

    root.mainloop()
