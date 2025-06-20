from typing import Annotated, Any, Dict, List, Optional, TypedDict

from loguru import logger


# Custom reducer function for merging dictionaries
def merge_dict_reducer(
    current_value: Dict[str, Any] | None, new_value: Dict[str, Any] | None
) -> Dict[str, Any]:
    """
    Reducer function to merge dictionaries for a LangGraph state channel.
    'current_value' is the accumulated dictionary in the state.
    'new_value' is the dictionary update from the current node for the 'input_args' key.
    Example: if a node returns {'input_args': {'new_key': 'new_val'}},
    then 'new_value' for the 'input_args' channel will be {'new_key': 'new_val'}.
    """

    if current_value is None:
        logger.debug("Reducer :: current_value is None, initializing to empty dict.")
        current_value = {}

    # If new_value is None, it means a node tried to write None to this channel's key.
    # In our case, ai_task_node always returns a dict for 'input_args', so new_value should be a dict.
    if new_value is None:
        logger.warning(
            "Reducer :: 'new_value' is None. Returning 'current_value' as is."
        )
        # Ensure a copy is returned as per LangGraph recommendations for safety
        final_dict = current_value.copy()
        logger.debug(
            f"Reducer EXIT (new_value was None) :: returning current_value copy ID: {id(final_dict)}, content: {final_dict}"
        )
        return final_dict

    if not isinstance(current_value, dict):
        logger.error(
            f"Reducer :: 'current_value' for 'input_args' is not a dict ({type(current_value)}). "
            f"Re-initializing to an empty dict before merging."
        )
        current_value = {}

    if not isinstance(new_value, dict):
        logger.error(
            f"Reducer :: 'new_value' to merge into 'input_args' is not a dict ({type(new_value)}). "
            f"Node returned incorrect type for 'input_args' key. Skipping merge."
        )
        final_dict = current_value.copy()
        logger.debug(
            f"Reducer EXIT (new_value bad type) :: returning current_value copy ID: {id(final_dict)}, content: {final_dict}"
        )
        return final_dict

    # Perform the merge
    merged_dict = current_value.copy()  # Start with a copy of the current state
    merged_dict.update(new_value)  # Apply the new updates

    return merged_dict


class ProcessSourceInput(TypedDict):
    content: str
    source: str


class ContentCreationState(TypedDict):
    context: List[ProcessSourceInput]
    input_args: Annotated[Dict[str, Any], merge_dict_reducer]
    output: Optional[str]
    input_args: Annotated[Dict[str, Any], merge_dict_reducer]
    output: Optional[str]
