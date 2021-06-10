import torch
import urllib
from torchvision import transforms
from PIL import Image
import matplotlib.pyplot as plt


def fromImageUrlToProbability(img_url):
    url, filename = (img_url, "twitter_image.jpg")

    try:
        urllib.URLopener().retrieve(url, filename)
    except:
        urllib.request.urlretrieve(url, filename)

    v1_resnet = torch.load("./v1_resnet.pt", map_location=torch.device('cpu'))
    v1_resnet.eval()

    # sample execution (requires torchvision)
    input_image = Image.open(filename)

    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    input_tensor = preprocess(input_image)
    input_batch = input_tensor.unsqueeze(0)  # create a mini-batch as expected by the model

    # plt.imshow(input_batch[0][0].cpu())
    # plt.show()

    # move the input and model to GPU for speed if available
    if torch.cuda.is_available():
        input_batch = input_batch.to('cuda')
        v1_resnet.to('cuda')

    with torch.no_grad():
        output = v1_resnet(input_batch)

    # The output has not normalized scores. To get probabilities, you can run a softmax on it.
    probabilities = torch.nn.functional.softmax(output[0], dim=0)
    probabilities = probabilities.cpu().numpy()

    return probabilities


#### Negatives ####
#img_url = "https://pictures.ssg-service.com/kat/kate-rising-mtb-s2e2_1600x750-landing-main-banner_2021_BIKE_SCOTT-Sports%20(1)_1800715_jpg_original_1.jpg"
#img_url = "https://i.insider.com/608d79c734af8d001859a6db?width=700"

#### Positives ####
#img_url = "https://static.coindesk.com/wp-content/uploads/2021/04/dogecoin.jpg"
#img_url = "https://pbs.twimg.com/media/E3drRMmWUAAJHYd?format=png&name=small"
# img_url = "https://estaticos-cdn.sport.es/clip/e578806c-5b90-45e4-bac2-55dce41bb832_media-libre-aspect-ratio_default_0.jpg"
#
# probability = fromImageUrlToProbability(img_url)
# print(probability)