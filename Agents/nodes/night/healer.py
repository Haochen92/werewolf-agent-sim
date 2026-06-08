from Agents.nodes.night.factory import make_night_act_node
from Agents.prompts import HEALER_NIGHT
from Agents.schemas import HealerOutput
from Agents.state import HealerNightGraph

healer_act = make_night_act_node(
    HEALER_NIGHT, HealerOutput, "healer_target", HealerNightGraph
)
