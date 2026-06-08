from Agents.nodes.night.factory import make_night_act_node
from Agents.prompts import INVESTIGATOR_NIGHT
from Agents.schemas import InvestigatorOutput
from Agents.state import InvestigatorNightGraph

investigator_act = make_night_act_node(
    INVESTIGATOR_NIGHT, InvestigatorOutput, "investigator_target", InvestigatorNightGraph
)
