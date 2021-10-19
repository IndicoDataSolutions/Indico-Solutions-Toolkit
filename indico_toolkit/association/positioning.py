class Positioning:
    def __init__(self):
        pass

    @staticmethod
    def positioned_below(main_loc: dict, compare_loc: dict) -> bool:
        pass

    def positioned_above(self, above_pos: dict, below_pos: dict) -> bool:
        if below_pos["page_num"] < above_pos["page_num"]:
            above = False
        elif self.xaxis_overlap(above_pos, below_pos):
            if (
                below_pos["page_num"] == above_pos["page_num"]
            ) and not self.yaxis_above(above_pos, below_pos):
                above = False
            else:
                above = True
        else:
            above = False
        return above

    @staticmethod
    def xaxis_overlap(pos1: dict, pos2: dict):
        return pos1["bbLeft"] < pos2["bbRight"] and pos2["bbLeft"] < pos1["bbRight"]

    @staticmethod
    def yaxis_above(above_pos: dict, below_pos, dict):
        return above_pos["bbTop"] > below_pos["bbTop"]

    @staticmethod
    def on_same_page(pos1: dict, pos2: dict):
        return pos1["page_num"] == pos2["page_num"]
