from scrapy.item import Item, Field


class Website(Item):

    name = Field()
    description = Field()
    url = Field()
    Stadt_URL = Field()
    URL_Datei = Field()
    URL_Text = Field()
    URL_Dateiname = Field()
    Format = Field()
    URL_PARENT = Field()
    Title_PARENT = Field()
