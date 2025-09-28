class Image:
    # TODO: Is this class actually in use / going to be used?
    def __init__(self, image_json):
        self.url = image_json['url']  # URL of the image.
        self.height = image_json['height']  # Height of the image.
        self.width = image_json['width']  # Width of the image.
