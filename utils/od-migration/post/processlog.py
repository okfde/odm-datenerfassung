with open("log.log", "rb") as infile:
    text = infile.read()
    parts = text.split("Examining")
    for part in parts:
        if "HTTP Error 409" in part:
            print "Conflict: " + part.split("\n")[0]
        elif "Error" in part:
            print "Other error:\n" + part
            