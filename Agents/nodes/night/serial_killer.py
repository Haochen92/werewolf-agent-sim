from Agents.nodes.night.factory import make_night_act_node
from Agents.prompts import SERIAL_KILLER_NIGHT
from Agents.schemas import SerialKillerOutput
from Agents.state import SerialKillerNightGraph

serial_killer_act = make_night_act_node(
    SERIAL_KILLER_NIGHT, SerialKillerOutput, "serial_killer_target", SerialKillerNightGraph
)
