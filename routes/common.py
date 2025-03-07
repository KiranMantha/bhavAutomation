def set_is_selected(records, strike_price, condition):
    """
    Helper function to set isSelectedRecord for records based on a condition.
    :param records: List of dictionaries containing option data
    :param strike_price: The strike price to compare
    :param condition: A lambda function to determine if the record meets the condition
    :return: Updated list of records with isSelectedRecord added
    """
    for record in records:
        record['isSelectedRecord'] = condition(record['StrkPric'], strike_price)
    return records