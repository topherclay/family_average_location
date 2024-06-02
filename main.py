import io
import pygeodesy as pgd
import folium
from PIL import Image
import os, os.path


# steps
# read input file with all the family names and GPS coords.
#   maybe off of a CSV file from Google sheets?
# makes an object for family member, order they were born in?, GPS location, certainty
# maybe diff algorithm for ordering them by distance to FAL
# generate a starting map based on boundaries of all data.
# add a family_member and then calculate the FAL and plot both on a new image.
# todo: have family members sort themselves by distance to FAL.
# todo: get STDdev of dataset so you can compare families lol.
# todo: animate it by adding kids one at a time and watching FAL drift.


class FamilyMember:
    def __init__(self, name, coordinates, location_name, certainty=0):
        self.name = name
        self.coordinates = coordinates
        self.location_name = location_name
        self.certainty = certainty
        self.vector = self.vectorize_location()

    def vectorize_location(self):
        return pgd.ellipsoidalNvector.LatLon(self.coordinates[0], self.coordinates[1])



def load_csv(file_name):
    # file_name = "scroobs.csv"

    with open(file_name, mode="r") as file:
        data = file.readlines()
        family_members = []
        for line in data[1:]:
            if line[0] == "#":

                continue
            data_points = line.split(",")
            name = data_points.pop(0)
            if name:
                location = data_points.pop(0)
                latitude = data_points.pop(0)
                longitude = data_points.pop(0)
                parent = data_points.pop(0)
                try:
                    certainty = int(data_points.pop(0))
                except ValueError:
                    certainty = 0
                _member = FamilyMember(name, (latitude, longitude), location, certainty=certainty)
                family_members.append(_member)
    return family_members


def determine_map_center(family_members):
    coordinates = [member.vector for member in family_members]
    boundaries = pgd.boundsOf(coordinates)

    first_point = (boundaries[0], boundaries[1])
    second_point = (boundaries[2], boundaries[3])

    first_vector = pgd.ellipsoidalNvector.LatLon(first_point[0], first_point[1])
    second_vector = pgd.ellipsoidalNvector.LatLon(second_point[0], second_point[1])
    center = pgd.ellipsoidalNvector.meanOf([first_vector, second_vector]).latlon

    return center, first_point, second_point


def save_to_image(map_to_be_saved, image_path="image.png"):
    print("converting map to image")
    image = map_to_be_saved._to_png(1)
    image = Image.open(io.BytesIO(image))
    print(f"saving to {image_path}")
    image.save(image_path)


def save_map_of_whole_family():
    # eventually delete this.
    _family = load_csv()

    center_coord, _, _ = determine_map_center(_family)
    _family_map = folium.Map(location=center_coord, zoom_start=4)
    folium.Marker(location=center_coord, tooltip="Center", icon=folium.Icon(color="red")).add_to(family_map)

    for member in _family:
        folium.Marker(location=[member.coordinates[0], member.coordinates[1]], tooltip=f"{member.name}").add_to(
            _family_map)

    points = [member.vector for member in _family]

    average = pgd.ellipsoidalNvector.meanOf(points).latlon

    print(average)

    folium.Marker(location=average, tooltip="average", icon=folium.Icon(color="green")).add_to(_family_map)

    _family_map.save("test_map.html")
    save_to_image(_family_map)


def create_map_centered_on_all_members(_family, zoom_level=4, add_center=True):
    center_coord, _, _ = determine_map_center(_family)
    _family_map = folium.Map(location=center_coord, zoom_start=zoom_level)
    if add_center:
        folium.Marker(location=center_coord, tooltip="Center", icon=folium.Icon(color="red")).add_to(_family_map)
    return _family_map


def add_member_to_map(parent_map, member_to_added: FamilyMember, marker_type="default"):
    member_location = member_to_added.coordinates[0], member_to_added.coordinates[1]

    if marker_type == "default":
        # folium.Marker(location=member_location, tooltip=f"{member.name}").add_to(parent_map)

        folium.CircleMarker(location=member_location,
                            radius=4,
                            weight=4).add_to(parent_map)



    if marker_type == "label":
        folium.Marker(location=member_location, icon=folium.Icon(color="purple")).add_child(folium.Popup(f"{member.name}")).add_to(parent_map)

        label = member.name
        if member.certainty > 1:
            label = label + "???"
        icon_length = len(label) * 7

        folium.map.Marker(location=member_location,
                          icon=folium.features.DivIcon(
                              icon_size=(icon_length, 10),
                              icon_anchor=(0, 0),
                              html=f"<div style='color: black; background: white'>{label}</div>",
                          )).add_to(parent_map)


def animate():
    images = []
    for file in os.listdir("maps"):
        if os.path.splitext(file)[1] == ".png":
            images.append(Image.open(f"maps/{file}"))

    images.append(images[-1])
    images.append(images[-1])
    images.append(images[-1])
    images.append(images[-1])
    images.append(images[-1])
    images.append(images[-1])
    images.append(images[-1])

    print(f"saving {len(images)} frames of animation...")
    images[0].save("out.gif", save_all=True, append_images=images[1:], loop=0, duration=500)
    print("done saving animation")




if __name__ == "__main__":
    csv_file = "scroobs.csv"
    html_file = f"{csv_file[:-4]}.html"
    print(f"working on {csv_file}. will save html to {html_file}")

    family = load_csv(file_name=csv_file)

    zoom_lvl = 7

    already_added_members = []
    image_count = 0
    for member in family:

        family_map = create_map_centered_on_all_members(family, zoom_level=zoom_lvl, add_center=False)



        # add current member as label
        add_member_to_map(family_map, member, marker_type="label")

        for old in already_added_members:
            add_member_to_map(family_map, old)

        already_added_members.append(member)

        # get FAL of everyone so far.
        points = [old.vector for old in already_added_members]
        if len(points) > 1:
            fam_avg_location = pgd.ellipsoidalNvector.meanOf(points).latlon
            folium.Marker(fam_avg_location, tooltip="average", icon=folium.Icon(color="green")).add_to(family_map)





        # save new map
        # family_map.save(f"maps/{image_count:05d}.html")
        save_to_image(family_map, f"maps/{image_count:05d}.png")
        image_count += 1


    family_map = create_map_centered_on_all_members(family, zoom_level=zoom_lvl, add_center=False)
    points = [old.vector for old in already_added_members]
    if len(points) > 1:
        fam_avg_location = pgd.ellipsoidalNvector.meanOf(points).latlon
        folium.Marker(fam_avg_location, tooltip="average", icon=folium.Icon(color="green")).add_to(family_map)
    for old in already_added_members:
        add_member_to_map(family_map, old)
    save_to_image(family_map, f"maps/{image_count:05d}.png")
    family_map.save(html_file)


    print(pgd.ellipsoidalNvector.meanOf(points).latlon)


    animate()
