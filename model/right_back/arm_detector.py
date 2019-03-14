import numpy as np
def get_angle(data_in):
    data = []
    for j in [1,2,3,4,8]:
        x = data_in[3*j]
        y = data_in[3*j + 1]
        data.append(x)
        data.append(y)
    x = np.array((data[4] - data[2],data[5] - data[3]))
    y = np.array((data[4] - data[6],data[5] - data[7]))
    Lx = np.sqrt(x.dot(x))
    Ly = np.sqrt(y.dot(y))
    cos_angle = x.dot(y)/(Lx*Ly)
    angle = np.arccos(cos_angle) * 360/2/np.pi
    x1 = np.array((data[0] - data[8],data[1] - data[9]))
    y1 = np.array((data[2] - data[4],data[3] - data[5]))
    Lx1 = np.sqrt(x1.dot(x1))
    Ly1 = np.sqrt(y1.dot(y1))
    cos_angle1 = x1.dot(y1)/(Lx1*Ly1)
    angle1 = np.arccos(cos_angle1) * 360/2/np.pi

    if not np.isnan(angle) and not np.isnan(angle1):
        return [int(np.round(angle1)),int(np.round(angle)),data[3],data[7]]

def arm_detect(list_in):
    if (list_in[0] < 70 and (list_in[1] >= 70 or list_in[1] <=20)) or list_in[2] < list_in[3] :
        flg = 1 #normal
    elif list_in[0] >= 70 and list_in[0] <= 150 and list_in[1] >= 100:
        flg = 2 #point_forward
    elif  list_in[0] >= 70 and list_in[0] <= 120 and list_in[1] >= 30 and  list_in[1] <= 100:
        flg = 3 #fist
    else:
        flg = 4 #other
    return flg