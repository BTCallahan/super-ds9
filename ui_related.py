from typing import Any, Iterable, Iterator, List, Optional, Tuple, Union
import tcod
from tcod import constants
from functools import wraps

IntOrString = Union[int, str]

confirm = {tcod.event.K_RETURN, tcod.event.K_KP_ENTER, tcod.event.K_RETURN2}

modifiers = {tcod.event.K_RALT, tcod.event.K_RCTRL, tcod.event.K_RSHIFT, tcod.event.K_LALT, tcod.event.K_LCTRL, tcod.event.K_LSHIFT}

minus = {tcod.event.K_MINUS, tcod.event.K_KP_MINUS, tcod.event.K_KP_PLUSMINUS}

plus = {tcod.event.K_KP_PLUS, tcod.event.K_PLUS}

delete_keys = {tcod.event.K_BACKSPACE, tcod.event.K_DELETE, tcod.event.K_KP_BACKSPACE}

cursor_move_left_right = {tcod.event.K_LEFT, tcod.event.K_RIGHT}
cursor_move_up_down = {tcod.event.K_UP, tcod.event.K_DOWN}

def clamp(*, number:int, min_value:int, max_value:int, wrap_around:bool):

    if number > max_value:
        # number = 23
        # min_value = 5
        # max_value = 21
        #
        # 5 + (23 - 21)
        # 5 + 2
        # 7
        number = (min_value + (number - max_value)) if wrap_around else max_value

    elif number < min_value:
        # number = 3
        # min_value = 5
        # max_value = 20
        #
        # 20 - (5 - 3)
        # 20 - 2
        # 18
        number = (max_value - (min_value - number)) if wrap_around else min_value

    return number

def send_text_after_call(funct):

    def send_text(self:"InputHanderer", *args, **kwargs):
        funct(self, *args, **kwargs)
        self.text = self.send()
        self.text_to_print = self.text
    return send_text

def check_for_unwanted_zeros(funct):

    def check_for_zeros(self:"NumberHandeler", *args, **kwargs):

        funct(self, *args, **kwargs)

        text_char_list_len = len(self.text_char_list)
        
        if text_char_list_len > 1 and self.text_char_list[0] == 0:
            last_digit_with_zero = 1
            for z in self.text_char_list[1:]:
                if z == 0:
                    last_digit_with_zero+=1
                else:
                    break
            self.text_char_list = self.text_char_list[last_digit_with_zero:]

    return check_for_zeros

def clamp_number_after_call(funct):

    def clamp_number(self:"NumberHandeler", *args, **kwargs):

        funct(self, *args, **kwargs)
        
        added = self.add_up() * (-1 if self.is_negitive else 1)

        clamped = clamp(number=added, min_value=self.min_value, max_value=self.max_value, wrap_around=self.wrap_around)

        broken_up = self.break_up(clamped)

        self.text_char_list = broken_up[:self.limit]

        self.is_negitive = clamped < 0
    
    return clamp_number

def clamp_number_after_call_strict(funct):

    def clamp_number(self:"NumberHandeler", *args, **kwargs):

        funct(self, *args, **kwargs)
        
        added = self.add_up() * (-1 if self.is_negitive else 1)

        clamped = clamp(number=added, min_value=self.min_value, max_value=self.max_value, wrap_around=False)

        broken_up = self.break_up(clamped)

        self.text_char_list = broken_up[:self.limit]

        self.is_negitive = clamped < 0
    
    return clamp_number

class SimpleElement:
    
    def __init__(
        self, 
        *, 
        x:int, y:int, height:int, width:int, title:str="", 
        text:str, 
        active_fg:Optional[Tuple[int,int,int]]=None, 
        bg:Optional[Tuple[int,int,int]]= None, 
        alignment:int=tcod.CENTER,
    ):
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.title = title
        self.text = text
        self.fg = active_fg
        self.bg = bg
        self.alignment=alignment
        
    def render(self, console: tcod.Console, *, 
        x:int=0, y:int=0, 
        fg:Optional[Tuple[int,int,int]]=None, bg:Optional[Tuple[int,int,int]]= None, 
        text:Optional[str]=None,
        alignment:Optional[int]=None
    ):
        console.draw_frame(
            x=x+self.x,
            y=y+self.y,
            width=self.width,
            height=self.height,
            title=self.title,
            fg=fg if fg else self.fg,
            bg=bg if bg else self.bg,
        )
        string_text = text if text is not None else self.text

        console.print_box(
            x=x+self.x+1,
            y=y+self.y+1,
            height=self.height-2,
            width=self.width-2,
            string=string_text,
            fg=fg if fg else self.fg,
            bg=bg if bg else self.bg,
            alignment=alignment if alignment is not None else self.alignment
        )
        
    def cursor_overlap(
        self, event: "tcod.event.MouseButtonDown", *, x:int=0, y:int=0
    ):
        return (
            x+self.x <= event.tile.x < x+self.x+self.width and 
            y+self.y <= event.tile.y < y+self.y+self.height
        )

class InteractiveElement(SimpleElement):
    
    def __init__(
        self, 
        *, 
        x:int, y:int, height:int, width:int, title:str="", 
        text:str,
        active_fg:Optional[Tuple[int,int,int]]=None, 
        bg:Optional[Tuple[int,int,int]]= None, 
        inactive_fg:Optional[Tuple[int,int,int]]=None, 
        initally_active:bool=True
    ) -> None:
        super().__init__(
            x=x, y=y, height=height, width=width, active_fg=active_fg, bg=bg, title=title, text=text
        )
        self.active_fg = active_fg
        self.inactive_fg = inactive_fg
        self._is_active = initally_active
        self.fg = active_fg if initally_active else inactive_fg 
    
    @property
    def is_active(self):
        return self._is_active
    
    @is_active.setter
    def is_active(self, value:bool):
        self._is_active = value
        self.fg = self.active_fg if self._is_active else self.inactive_fg 
    
    
class ButtonBox(InteractiveElement):

    def __init__(
        self, 
        *, 
        x:int, y:int, height:int, width:int, title:str="", 
        text:str, 
        active_fg:Optional[Tuple[int,int,int]]=None, 
        bg:Optional[Tuple[int,int,int]]= None, 
        inactive_fg:Optional[Tuple[int,int,int]]=None, 
        initally_active:bool=True,
        alignment:int=constants.CENTER
    ) -> None:
        super().__init__(
            x=x, y=y, height=height, width=width, title=title, 
            active_fg=active_fg, bg=bg, inactive_fg=inactive_fg, initally_active=initally_active, text=text
        )
        self.alignment = alignment    
        
    def render(self, console: tcod.Console, *, 
        x:int=0, y:int=0, 
        fg:Optional[Tuple[int,int,int]]=None, bg:Optional[Tuple[int,int,int]]= None, 
        text:Optional[str]=None, cursor_position:Optional[int]=None
    ):
        fg, bg = (fg if fg else self.fg), (bg if bg else self.bg)
        
        console.draw_frame(
            x=x+self.x,
            y=y+self.y,
            width=self.width,
            height=self.height,
            title=self.title,
            fg=fg,
            bg=bg,
        )
        string_text = text if text is not None else self.text

        console.print_box(
            x=x+self.x+1,
            y=y+self.y+1,
            height=self.height-2,
            width=self.width-2,
            string=string_text,
            fg=fg,
            bg=bg,
            alignment=self.alignment, 
        )

        if cursor_position is not None:

            try:
                char = string_text[cursor_position]
            except IndexError:
                char = " "
            
            console.print(
                x=self.x + 1 + (self.width - 2) + cursor_position - len(string_text) if 
                self.alignment == constants.RIGHT else 
                self.x + 1 + cursor_position,
                y=self.y+1,
                string=char,
                fg=bg,
                bg=fg,
            )
    
    def cursor_overlap(self, event: "tcod.event.MouseButtonDown",*, x:int=0, y:int=0) -> bool:

        return x+self.x <= event.tile.x < x+self.x+self.width and y+self.y <= event.tile.y < y+self.y+self.height

class ScrollingTextBox(ButtonBox):
    
    def __init__(
        self, 
        *, 
        x: int, y: int, 
        height: int, width: int, 
        title: str = "", 
        total_text: Iterable[str], 
        active_fg: Optional[Tuple[int, int, int]] = None, 
        bg: Optional[Tuple[int, int, int]] = None, 
        inactive_fg: Optional[Tuple[int, int, int]] = None, 
        initally_active: bool = True,
        lines_to_scroll:int, alignment:int=tcod.LEFT
        
        ) -> None:
        
        self.total_text = total_text
        
        self._index = 0
        self.lines_to_scroll = lines_to_scroll
        
        try:
            text = "\n".join(self.total_text[self._index : self._index + height])
        except IndexError:
            text = "\n".join(self.total_text[self._index : ])
        
        super().__init__(
            x=x, y=y, height=height, 
            width=width, title=title, 
            text=text, active_fg=active_fg, bg=bg, inactive_fg=inactive_fg, 
            initally_active=initally_active, alignment=alignment
        )
        
        self._max_index = max(0, len(self.text) - (height // 2))
    
    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value:int):
        old = self._index
        if value < 0:
            self._index = 0
        else:
            self._index = self._max_index if value > self._max_index else value
        if old != self._index:
            try:
                self.text = "\n".join(self.total_text[self._index : self._index + self.height])
            except IndexError:
                self.text = "\n".join(self.total_text[self._index : ])
    
    def handle_key(self, event: "tcod.event.KeyDown") -> None:
        
        if event.sym == tcod.event.K_UP:
            self.index -= 1
        elif event.sym == tcod.event.K_PAGEUP:
            self.index -= self.lines_to_scroll
        elif event.sym == tcod.event.K_DOWN:
            self.index += 1
        elif event.sym == tcod.event.K_PAGEDOWN:
            self.index += self.lines_to_scroll


class BooleanBox(ButtonBox):
    
    def __init__(self, *, x: int, y: int, height: int, width: int, title: str = "", active_text: str, inactive_text:str = None, active_fg: Optional[Tuple[int, int, int]] = None, bg: Optional[Tuple[int, int, int]] = None, inactive_fg: Optional[Tuple[int, int, int]] = None, initally_active: bool = True, alignment: int = constants.LEFT) -> None:
        
        text = active_text if initally_active else inactive_text
        
        super().__init__(x=x, y=y, height=height, width=width, title=title, text=text, active_fg=active_fg, bg=bg, inactive_fg=inactive_fg, initally_active=initally_active, alignment=alignment)
        
        self.active_text = active_text
        self.inactive_text = inactive_text
    
    @property
    def is_active(self):
        return self._is_active
    
    @is_active.setter
    def is_active(self, value:bool):
        
        self._is_active = value
        self.fg = self.active_fg if self._is_active else self.inactive_fg 
        self.text = self.active_text if self._is_active else self.inactive_text
    
    

class InputHanderer(ButtonBox):
    """Semi-abstract class with unimplemented methods

    Raises:
        NotImplementedError: [description]
        NotImplementedError: [description]
        NotImplementedError: [description]
        NotImplementedError: [description]

    Returns:
        [type]: [description]
    """

    text_to_print = ""
    cursor = 0

    def __init__(
        self, 
        *,
        limit:int, 
        text_char_list:Optional[List[IntOrString]] = None,
        x:int, y:int,
        height:int, width:int, 
        title:str,
        active_fg:Tuple[int, int, int], inactive_fg:Tuple[int, int, int], bg:Tuple[int, int, int],
        initally_active:bool=True,
        alignment = tcod.LEFT
    ):
        super().__init__(
            x=x, y=y, 
            height=height, width=width, 
            title=title, text="", 
            active_fg=active_fg, inactive_fg=inactive_fg, bg=bg,
            initally_active=initally_active, 
            alignment=alignment
        )
        self.limit = limit
        self.text_char_list: List[IntOrString] = text_char_list if text_char_list is not None else []
        
        self.text = self.send()
        self.text_to_print = self.text

    def set_text(self, character:IntOrString):
        raise NotImplementedError("You are trying to access the unimplemented method 'set_text' from an abstract 'InputHanderer' object")

    @property
    def number_of_chars(self):
        return len(self.text_char_list)

    @property
    def is_empty(self):
        return len(self.text_char_list) == 0

    def handle_key(self, event: tcod.event.KeyDown):
        raise NotImplementedError("You are trying to access the unimplemented method 'handle_key' from an abstract 'InputHanderer' object")

    def translate_key(self, event: tcod.event.KeyDown):
        raise NotImplementedError("You are trying to access the unimplemented method 'translate_key' from an abstract 'InputHanderer' object")
    
    def delete(self, reverse:bool=False):
        """Deletes a character in the list self.text_char_list.

        Args:
            reverse (bool, optional): If this is true, it will be treated as if the user clicked the 'delete' key instead of the 'backspace' key. Defaults to False.

        Returns:
            (bool): True if the deletion attempt was sucessful, False if not.
        """
        if reverse and self.number_of_chars > self.cursor:
            #print("Delete")
            self.text_char_list.pop(self.cursor)
            return True
        if not reverse and self.cursor > 0 and self.number_of_chars >= 1:
            #print("Backspace")
            self.text_char_list.pop(self.cursor - 1)

            self.cursor -= 1
            return True
        return False
    
    def get_char_after_cursor(self):

        if self.number_of_chars == self.cursor:
            return " "
        return str(self.text_char_list[self.cursor])
        
    def cursor_move(self, direction:int) -> bool:

        if direction == tcod.event.K_LEFT and self.cursor > 0:
            self.cursor -= 1
            return True
        if direction == tcod.event.K_RIGHT and self.cursor < self.number_of_chars:
            self.cursor += 1
            return True
        return False
    
    def send(self) -> IntOrString:
        raise NotImplementedError("You are trying to access the unimplemented method 'send' from an abstract 'InputHanderer' object")
    
    def insert(self, *, character:IntOrString, position:Optional[int]=None) -> bool:
        position = position if position is not None else self.cursor
        if self.number_of_chars < self.limit:
            self.text_char_list.insert(self.cursor, character)
            self.cursor += 1
            return True
        return False
    
    def print_text_to_screen(self, console:tcod.Console, x:int, y:int, 
    fg:Optional[Tuple[int,int,int]]=None, bg:Optional[Tuple[int,int,int]]=None) -> None:
        raise NotImplementedError("You are trying to access the unimplemented method 'print_text_to_screen' from an abstract 'InputHanderer' object")

    def render(
        self, 
        console: tcod.Console, 
        *, 
        x: int = 0, y: int = 0, 
        fg: Optional[Tuple[int, int, int]] = None, bg: Optional[Tuple[int, int, int]] = None, text: Optional[str] = None, 
        cursor_position: Optional[int] = None
    ):
        super().render(
            console, 
            x=x, y=y, 
            fg=fg, bg=bg, 
            text=text if text else self.text_to_print, 
            cursor_position=cursor_position if cursor_position else self.cursor
        )

class TextHandeler(InputHanderer):
    """Handels string operations

    Args:
        limit (int): The maxinum nuber of characters that may be present.
        text_char_list (List[IntOrString], optional): A list of strings. Each string must contain only one character. Defaults to None.
    """

    def __init__(
        self, 
        *,
        limit: int, 
        text_char_list: Optional[List[IntOrString]] = None,
        x:int, y:int,
        height:int, width:int, 
        title:str,
        active_fg:Tuple[int, int, int], inactive_fg:Tuple[int, int, int], bg:Tuple[int, int, int],
        initally_active:bool=True,
        alignment = tcod.LEFT
    ):
        super().__init__(
            limit=limit, 
            text_char_list=text_char_list,
            x=x, y=y,
            height=height, width=width,
            title=title,
            active_fg=active_fg, inactive_fg=inactive_fg, bg=bg,
            initally_active=initally_active, alignment=alignment
        )
        self.text = "".join(self.text_char_list)
        self.text_to_print = self.text

    def set_text(self, character: str):
        if len(character) > self.limit:
            character = character[:self.limit]

        self.text_to_print = character
        self.text_char_list = list(character)

    def send(self) -> str:
        return "".join(self.text_char_list)

    @send_text_after_call
    def delete(self, reverse: bool = False):
        return super().delete(reverse=reverse)

    def handle_key(self, event: tcod.event.KeyDown):
        
        if event.sym in cursor_move_left_right:
            return self.cursor_move(event.sym)
        
        elif event.sym in delete_keys:
            return self.delete(event.sym == tcod.event.K_DELETE)
        else:
            key = self.translate_key(event)
            if key is not None:
                return self.insert(character=key)
        return False

    def translate_key(self, event: tcod.event.KeyDown):

        if event.sym in {tcod.event.K_HOME, tcod.event.K_END, 
            tcod.event.K_PAGEUP, tcod.event.K_PAGEDOWN, 
            tcod.event.K_LEFT, tcod.event.K_RIGHT, tcod.event.K_UP, tcod.event.K_DOWN,
            tcod.event.K_TAB, tcod.event.K_KP_TAB,
            tcod.event.K_ESCAPE, 
            tcod.event.K_CLEAR, tcod.event.K_KP_CLEAR, 
            tcod.event.K_RETURN, tcod.event.K_KP_ENTER}:
            return None
        
        if event.sym in modifiers:
            return None

        if event.sym in {tcod.event.K_KP_PERIOD, tcod.event.K_KP_PLUS, tcod.event.K_KP_MINUS}:
            return chr(event.sym - 1073741912) 

        if event.sym in range(tcod.event.K_KP_1, tcod.event.K_KP_9 + 1):
            return chr(event.sym - 1073741912)
        if event.sym == tcod.event.K_KP_0:
            return "0"
        if event.sym == tcod.event.K_SPACE:
            return " "
        
        return chr(event.sym - (32 if event.mod & tcod.event.KMOD_SHIFT != 0 or event.mod & tcod.event.KMOD_CAPS != 0 else 0))
        
    @send_text_after_call
    def insert(self, *, character:str, position:Optional[int]=None) -> bool:

        if not isinstance(character, str):
            raise TypeError("The paramiter 'character' must be a string")
            
        if len(character) != 1:
            raise ValueError(f"The string 'character' must have only one character. You are passing in a string with {len(character)} characters")
        
        return super().insert(character=character, position=position)
        
    def print_text_to_screen(self, console:tcod.Console, x:int, y:int, 
    fg:Optional[Tuple[int,int,int]]=None, bg:Optional[Tuple[int,int,int]]=None) -> None:

        s = self.text_to_print if 0 < self.number_of_chars else " "
        try:
            s2 = s[self.cursor]
        except IndexError:
            s2 = " "

        console.print(x=x,y=y, string=s, fg=fg, bg=bg, bg_blend=constants.BKGND_SET)

        console.print(x=x+self.cursor, y=y, string=s2, fg=bg, bg=fg)
    
    

"""
1, 1 (1*1)
2, 2 (1*2)
3, 6 (2*3)
4, 24 (6*4)
5, 120, (24*5)
6, 720, (120*6)
7, 5040  (720*7)
"""

class NumberHandeler(InputHanderer):

    def __init__(
        self, 
        *,
        limit:int, 
        max_value:int, min_value:int, 
        wrap_around:bool=False, 
        starting_value:Optional[int]=None,
        x:int, y:int,
        height:int, width:int, 
        title:str,
        active_fg:Tuple[int, int, int], inactive_fg:Tuple[int, int, int], bg:Tuple[int, int, int],
        initally_active:bool=True, alignment = tcod.RIGHT
    ) -> None:
        if min_value > max_value:
            min_value, max_value = max_value, min_value

        s_value = starting_value if starting_value is not None else min_value
        
        self.is_negitive = s_value < 0
        super().__init__(
            limit=limit,
            x=x, y=y,
            height=height, width=width,
            title=title, 
            active_fg=active_fg, inactive_fg=inactive_fg, bg=bg,
            initally_active=initally_active, alignment=alignment
        )
        self.max_value = max_value
        self.min_value = min_value
        self.wrap_around = wrap_around
        
        self.text_char_list = self.break_up(s_value)

        self.text_to_print = ("-" if self.is_negitive else "") + "".join([str(i) for i in self.text_char_list])

    def set_text(self, character: int):
        """Takes a intiger and breaks it up and assigns it to the self.text_char_list. Calls 'self.check_if_is_in_bounds()' afterwards.

        Args:
            character (int): The intiger that is to broken up and assigned
        """

        self.is_negitive = character < 0

        self.text_char_list = self.break_up(character)
        #print(f"New char list {self.text_char_list}")
        self.check_if_is_in_bounds()
        n_of_chars = self.number_of_chars
        if self.cursor > n_of_chars:
            self.cursor = n_of_chars
        #print(f"New char list {self.text_char_list}, new chars: {character}")

    @property
    def can_be_negative(self):
        return self.min_value < 0
    
    @property
    def can_be_positive(self):
        return self.max_value > -1

    def handle_key(self, event: tcod.event.KeyDown):

        if event.sym in plus and self.can_be_positive:
            self.is_negitive = False
            self.check_if_is_in_bounds()
        elif event.sym in minus:
            if not self.is_negitive and self.can_be_negative:
                self.is_negitive = True
                self.check_if_is_in_bounds()
            elif self.is_negitive and self.can_be_positive:
                self.is_negitive = False
                self.check_if_is_in_bounds()
        elif event.sym in cursor_move_left_right:
            self.cursor_move(event.sym)
        elif event.sym in cursor_move_up_down:
            self.increment(is_up=event.sym == tcod.event.K_UP, cursor=self.cursor)
        elif event.sym in delete_keys:
            self.delete(event.sym == tcod.event.K_DELETE)
        else:
            key = self.translate_key(event)
            if key is not None:
                self.insert(character=key)

    def translate_key(self, event: tcod.event.KeyDown):

        if event.sym in range(tcod.event.K_0, tcod.event.K_9 + 1):
            return event.sym - 48
        if event.sym in range(tcod.event.K_KP_1, tcod.event.K_KP_9 + 1):
            return event.sym - 1073741912
        if event.sym in {tcod.event.K_KP_0, tcod.event.K_KP_00, tcod.event.K_KP_000}:
            return 0
        return None

    def send(self) -> str:
        
        return ("-" if self.is_negitive else "") + "".join([str(i) for i in self.text_char_list])
    
    @send_text_after_call
    @clamp_number_after_call_strict
    @check_for_unwanted_zeros
    def delete(self, reverse: bool = False):

        if super().delete(reverse=reverse):
            if self.is_empty:
                self.text_char_list.append(0)
            return True
        return False

    @send_text_after_call
    @clamp_number_after_call
    @check_for_unwanted_zeros
    def increment(self, *, is_up:bool=True, cursor:Optional[int]=None):
        """Increments the number based on the position of the cursor. If the cursor is all the way to the left, and the leftmost digit is 5, then the leftmost digit will be incremented 'up' to 6. If 

        Calls self.check_if_is_in_bounds() at the end.

        Args:
            is_up (bool, optional): This determins if the digit will be incremented up or down. Defaults to True.
            cursor (Optional[int], optional): If this is None, then self.cursor will be used. Defaults to None.
        """

        cursor = cursor if cursor is not None else self.cursor

        def _increment(*, is_up:bool, cursor:int):

            up_or_down = (1 if is_up else -1)

            try:
                old = self.text_char_list[cursor]
                self.text_char_list[cursor]+=up_or_down
                new_ = self.text_char_list[cursor]

                if is_up and old == 9 and new_ == 10:
                    self.text_char_list[cursor] = 0

                    if cursor - 1 >= 0:

                        _increment(is_up=is_up, cursor=cursor-1)

                    elif cursor == 0 and self.number_of_chars < self.limit:

                        self.insert(character=1)

                elif not is_up and old == 0 and new_ == -1:
                    self.text_char_list[cursor] = 9

                    if cursor < self.limit:

                        _increment(is_up=is_up, cursor=cursor-1)
            except IndexError:
                pass
                
                #elif cursor == self.limit and self.number_of_chars < self.limit:

        _increment(is_up=is_up, cursor=cursor)

    @send_text_after_call
    def check_if_is_in_bounds(self):

        added = self.add_up() * (-1 if self.is_negitive else 1)

        clamped = clamp(number=added, min_value=self.min_value, max_value=self.max_value, wrap_around=self.wrap_around)

        self.is_negitive = clamped < 0

        #print(f"In bounds: {clamped} ")

        self.text_char_list = self.break_up(clamped)

    def add_up(self, to_add:Optional[Iterator[int]]=None) -> int:

        to_add = self.text_char_list if to_add is None else to_add

        total = 0
        for i, n in enumerate(reversed(to_add)):
            total += n * pow(10, i)
        return total
        
        #return reduce(lambda a,b: b * pow(10, a), enumerate(reversed(self.int_list)))
    @staticmethod
    def break_up(num:int):
        """Breaks up an intiger into a list of ints, each of which is less then 10 and greater to or equal to 0.

        Args:
            num (int): The intiger that is to be broken up

        Returns:
            list[int]: A list of intigers.

        How it works:

        the argument 'num' is converted to a positive number. If it is lower then 10, it will be convirted directly into a list and returned. Otherwise, the sub function, __break_up will be called.

        c = 0

        p = pow(10, c)

        while p <= num:

            yield (num % pow(10, c+1)) // p

            c += 1

            p = pow(10, c)
        
        so assuming that num is 280...

        c = 0

        p = pow(10, 0)

        p = 1

        while 1 <= 280:

            yield (280 % pow(10, 0+1)) // 1

            (280 % 10) // 1

            0 // 1

            yield 0

            c += 1

            c = 1

            p = pow(10, 1)

            p = 10
        
        (second loop)

        while 10 <= 280:

            yield (280 % pow(10, 1+1)) // 10

            (280 % 100) // 10

            80 // 10

            yield 8
        """
        #print(f"Num to be broken up: {num}")
        num = abs(num)

        if num < 10:
            return [num]

        def __break_up():
            c = 0

            p = pow(10, c)

            while p <= num:

                yield (num % pow(10, c+1)) // p

                c += 1

                p = pow(10, c)

        bu:List[int] = list(__break_up())
        #print(f"{bu}")
        bu.reverse()
        #print(f"{bu}")
        return bu

    @send_text_after_call
    @clamp_number_after_call_strict
    @check_for_unwanted_zeros
    def insert(self, *, character:int, position:Optional[int]=None) -> bool:

        if not isinstance(character, int):
            raise TypeError("The paramiter 'character' must be a integer")

        if character not in range(0,10):
            raise ValueError(
                f"The integer 'character' must have a value not more then 9 and not less then 0. You are passing in an int with a value of {character}"
            )
        
        #print(f"Before insert: {self.text_char_list} {character}")

        if not (character == 0 and self.cursor == 0) and super().insert(character=character, position=position):
            """
            total = self.add_up()
            print(f"Total: {total}, Min: {self.min_value}, Max: {self.max_value}")
            if not (self.min_value <= total <= self.max_value):
                
                Assume that self.value is 6, value is -9, self.max_value is 12, and self.min_value is 0
                new_value = self.value + value
                new_value = 6 + -9
                new_value is -3
                if self.wrap_around is true, then 
                self.value = self.max_value + (new_value - self.min_value)
                self.value = 12 + (-3 - 0)
                self.value = 12 + (-3)
                self.value is now 9

                Assume that self.value is 18, value is 5, self.max_value is 20, and self.min_value is 5
                new_value is 23
                if self.wrap_around is true, then 
                self.value = self.min_value + (new_value - self.max_value)
                self.value = 5 + (23 - 20)
                self.value = 5 + 3
                self.value is now 8
                

                add_stuff_to_me, value_if_no_wrap_around = (self.max_value, self.min_value) if total < self.min_value else (self.min_value, self.max_value)

                total = add_stuff_to_me + (total - value_if_no_wrap_around) if self.wrap_around else value_if_no_wrap_around
                
                if total < self.min_value:

                    total = self.max_value + (total - self.min_value) if self.wrap_around else self.min_value

                else:

                    total = self.min_value + (total - self.max_value) if self.wrap_around else self.max_value
                broken_up = self.break_up(total)

                self.text_char_list = broken_up
                #self.check_if_is_in_bounds()
            """
                
            #print(f"After insert: {self.text_char_list}")
            return True
        return False


class Selector(InteractiveElement):
    """Allows the user to select an item from a list.
    
    Args:
        x (int): X location
        y (int): Y location
        height (int): Height in units
        width (int): Width in units
        index_items (Tuple[str]): An itterable containing strings that is used to create the text block
        keys (Tuple[Any]): An itterable of keys. This is used by the property 'index_key', which returns key will be returned
        title (str, optional): The title of the element. Defaults to "".
        index (int, optional): The index. Defaults to 0.
        wrap_item (bool, optional): If set to true, incrementing the index when it is at the max value will reset it to zero. Defaults to False.
    
    """
    
    def __init__(
        self, 
        *, 
        x:int, y:int, height:int, width:int, 
        active_fg:Optional[Tuple[int,int,int]]=None, 
        bg:Optional[Tuple[int,int,int]]= None, 
        inactive_fg:Optional[Tuple[int,int,int]]=None, 
        initally_active:bool=True,
        index_items:Iterable[str], keys:Iterable[Any],
        title:str="", index:int=0, wrap_item:bool=False
    ):
        width_2 = width - 2
        
        trimmed = [
            s[:width_2] for s in index_items
        ]
        trimmed_ = trimmed[:height-2]
        
        joined_items = "\n".join(
            [f"{i:<{width_2}}" for i in trimmed_]
        )
        super().__init__(
            x=x, y=y, height=height, width=width, title=title, text=joined_items,
            active_fg=active_fg, bg=bg, inactive_fg=inactive_fg, initally_active=initally_active
        )
        self.index = index
        self.index_items = index_items
        self.trimmed = trimmed
        self.max_index = len(self.index_items)
        self.width_2 = width_2
        self.joined_items = joined_items
        self.keys = keys
        self.wrap_item = wrap_item
        self.offset = 0

    @property
    def index_key(self):
        return self.keys[self.index]
    
    def render(self, console: tcod.Console, *, 
            fg:Optional[Tuple[int,int,int]]=None, bg:Optional[Tuple[int,int,int]]=None,
            x=0, y=0
        ):
        console.draw_frame(
            x=self.x+x, y=self.y+y,
            title=self.title, 
            width=self.width,
            height=self.height,
            fg=fg if fg else self.fg, 
            bg=bg if bg else self.bg,
        )
        console.print_box(
            x=self.x+1+x,y=self.y+1+y,
            height=self.height-2,
            width=self.width-2,
            fg=fg if fg else self.fg, 
            bg=bg if bg else self.bg,
            string=self.text
        )
        console.print(
            x=self.x + 1 + x,
            y=self.y + 1 + self.index + y - self.offset,
            string=f"{self.index_items[self.index]:<{self.width_2}}",
            bg=fg if fg else self.fg, 
            fg=bg if bg else self.bg
        )
    
    def handle_click(self, event: "tcod.event.MouseButtonDown"):
        
        y_ = event.tile.y - (self.y + 1)
        
        if y_ < self.max_index and self.index != y_:
            self.index = y_
            return True
        return False
        
    def cursor_overlap(
        self, event: "tcod.event.MouseButtonDown", *, x:int=0, y:int=0
    ):
        return (
            x+self.x+1 <= event.tile.x < x+self.x+self.width - 1 and 
            y+self.y+1 <= event.tile.y < y+self.y+self.height - 1
        )
    
    def handle_key(self, event: tcod.event.KeyDown):
        
        re_render = False
        
        if event.sym == tcod.event.K_UP:
            
            self.index -= 1
            
            if self.index - self.offset < 0:
                
                self.offset -= 1
                
                re_render = True
            
            if self.index < 0:
                # assume that self.height is 18, self.offset is 4, and self.trimmed has 26 entries
                # len(self.trimmed[4:4 + (18-2)])
                # len(self.trimmed[4:4 + (16)])
                # len(self.trimmed[4:20])
                # 16
                
                l = len(self.trimmed[self.offset:self.offset + (self.height-2)])
                
                self.index, self.offset = (
                    self.max_index - 1, self.max_index - (1 + len(self.trimmed[:self.height-2]))
                ) if self.wrap_item else (0, 0)
                
                re_render = True
                
        elif event.sym == tcod.event.K_DOWN:
            
            self.index += 1
            
            l = len(self.trimmed[self.offset:self.offset + (self.height-2)])
            
            if self.index - self.offset >= l:
                
                self.offset += 1
                
                re_render = True
        
            if self.index >= self.max_index:
                
                self.index, self.offset = (0, 0) if self.wrap_item else (self.max_index - 1, self.offset)
                
                re_render = True
        
        if re_render:
            
            trimmed_ = self.trimmed[self.offset:self.offset + (self.height - 2)]
        
            joined_items = "\n".join(
                [f"{i:<{self.width_2}}" for i in trimmed_]
            )
            self.text = joined_items
        
        