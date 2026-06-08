from Agents.nodes.night.factory import make_night_act_node
from Agents.prompts import VIGILANTE_NIGHT
from Agents.schemas import VigilanteOutput
from Agents.state import VigilanteNightGraph

vigilante_act = make_night_act_node(
    VIGILANTE_NIGHT, VigilanteOutput, "vigilante_target", VigilanteNightGraph
)
