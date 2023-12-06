ANALYZE_STATE_FUNCTION_NAME = "analyze_query"
ANALYZE_STATE_FUNCTION_DESCRIPTION = "Use this function to analyze the user's query and get the short " \
                                     "description of the guide he needs. Extract only the information that " \
                                     "represents the guide. Greetings and side conversations are unimportant"

INPUT_STATE_FUNCTION_NAME = "extract_vars"
INPUT_STATE_FUNCTION_DESCRIPTION = "Use this function to extract the important information from the user's query"

GUIDE_STATE_FUNCTION_NAME = "guide"
GUIDE_STATE_FUNCTION_DESCRIPTION = "Use this function to extract the current step of the guide and to understand " \
                                   "whether the user has any issues"

SWITCH_STATE_FUNCTION_NAME = "resolve"
SWITCH_STATE_FUNCTION_DESCRIPTION = "analyze the user's wish"

ISSUES_STATE_FUNCTION_NAME = "troubleshoot"
ISSUES_STATE_FUNCTION_DESCRIPTION = "Use this function to understand from the user query whether the troubleshooting " \
                                    "is finished or the user stops it"

description_os = "Extracted operating system from user input. Put None if no operating system given by user."
description_dhcp = "If the user has configured DHCP before, or not. Default value is -1"
