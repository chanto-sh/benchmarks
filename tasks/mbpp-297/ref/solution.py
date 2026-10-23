
def flatten_list(list1):
	result = []
	for item in list1:
		if isinstance(item, list):
			result.extend(flatten_list(item))
		else:
			result.append(item)
	return result
