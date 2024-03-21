from enum import Enum

try:
    from typing import Literal, Union
except ImportError:
    from typing_extensions import Literal
from typing import Optional


class ConversationStyle(Enum):
    creative = [
        "fluxsydney",
        "nojbf",
        "iyxapbing",
        "iycapbing",
        "dgencontentv3",
        "nointernalsugg",
        "disable_telemetry",
        "machine_affinity",
        "streamf",
        "codeint",
        "langdtwb",
        "fdwtlst",
        "fluxprod",
        "eredirecturl",
        "deuct3",
        # "nosearchall"
    ]
    balanced = [
        "fluxsydney",
		"nojbf", # no jailbreak filter
		"iyxapbing",
		"iycapbing",
		"dgencontentv3",
		"nointernalsugg",
		"disable_telemetry",
		"machine_affinity",
		"streamf",
		"langdtwb",
		"fdwtlst",
		"fluxprod",
		"eredirecturl",
		"gptvnodesc",  # may related to image search
		"gptvnoex",    # may related to image search
		"codeintfile", # code interpreter + file uploader
		"sdretrieval", # retrieve upload file
		"gamaxinvoc",  # file reader invocation
		"ldsummary",   # our guess: long document summary
		"ldqa",        # our guess: long document quality assurance
        "galileo",
        "gldcl1p",
        "gpt4tmncnp",
    ]
    precise = [
        "fluxsydney",
        "nojbf",
        "iyxapbing",
        "iycapbing",
        "dgencontentv3",
        "nointernalsugg",
        "disable_telemetry",
        "machine_affinity",
        "streamf",
        "codeint",
        "langdtwb",
        "fdwtlst",
        "fluxprod",
        "eredirecturl",
        "deuct3",
        # Precise
        "h3precise",
        "gpt4tmncnp",
    ]


CONVERSATION_STYLE_TYPE = Optional[
    Union[ConversationStyle, Literal["creative", "balanced", "precise"]]
]
