#script that reads an OQ nrml source model
#reduces it to sources which extend into a given region (ONLY 2D!! surface distance)
#and return a reduced source model

from bs4 import BeautifulSoup
import re

###Config###
output='reduced_source.xml'

#two options either distance or region
ftype = 'region'
xr = [-75,-68]
yr = [-36,-30]
##buf buffer in km
#ftype = 'distance'
#d=200
##site
#xt=-71.5730623712764
#yt=-33.1299174879672
#x = 32
#y = 32
#source model
#sm = "source_model_frankel_gruenthal_b108_s20.xml"
sm = "sara_source_model.xml"

###Functions###

def haversine(x1,y1,x2,y2):
    '''
    Haversine formula to calculate distance
    '''
    import math
    #convert to rad
    deg2rad = math.pi/180
    x1 = float(x1)*deg2rad
    x2 = float(x2)*deg2rad
    y1 = float(y1)*deg2rad
    y2 = float(y2)*deg2rad
    #central angle using haversine
    dsig = 2*math.asin(math.sqrt((math.sin(abs(y1-y2)/2))**2 + math.cos(y1)*math.cos(y2)*(math.sin(abs(x1-x2)/2))**2))
    #distance
    return 6371*dsig

def closeby(x1,y1,x2,y2,d):
    '''
    Boolean check if distance between points <= d
    '''
    #deal with lists here
    try:
        #x1,y1 are lists
        x1[0]
        return any([d > haversine(float(x),float(y),float(x2),float(y2)) for x,y in zip(x1,y1)])
    except:
        #x2,y2 are lists
        try:
            x2[0]
            return any([d > haversine(float(x1),float(y1),float(x),float(y)) for x,y in zip(x2,y2)])
        except:
            #None are lists
            try:
                return d > haversine(float(x1),float(y1),float(x2),float(y2))
            except:
                raise Exception('No distance calculation possible:',x1,y1,x2,y2)

def within(x,y,xmin,xmax,ymin,ymax):
    '''
    Checks if a point is within a rectangular region
    '''
    return (x<=xmax) & (x>=xmin) & (y<=ymax) & (y>=ymin)

def intersects_poly(x,y,x2,y2):
    '''
    Checks if geometry intersects with a polygon region
    '''
    #x,y are lists xmin,xmax,ymin,ymax
    #x2,y2 are lists (source coordinates)
    try:
        x2[0]
        return any([within(float(xs),float(ys),x[0],x[1],y[0],y[1]) for xs,ys in zip(x2,y2)])
    except:
        #No list only point
        try:
            return within(float(x2),float(y2),x[0],x[1],y[0],y[1])
        except:
            raise Exception('No within calculation possible:',x,y,x2,y2)

###Read Source Model###
with open(sm) as f:
    doc = f.read()
soup = BeautifulSoup(doc, 'xml')

##POINT SOURCES
print('###\nProcessing {}\n###\n'.format(sm))
#find all position informations
print('---\nPoint sources\n---\n'.format(sm))
#positions = soup.find_all('gml:pos')
#print('Found {} point sources'.format(len(positions)))
point_sources = soup.find_all('pointSource')
print('Found {} point sources'.format(len(point_sources)))

count = 0
for ps in point_sources:
    positions=ps.find_all('gml:pos')
    #get coordinates
    coords = [p.contents[0].strip().split(' ') for p in positions]
    if ftype=='distance':
        #check if at least one is close enough to site
        close = [closeby(xt,yt,cp[0:][::2],cp[1:][::2],d) for cp in coords]
        if any(close):
            count=+1
        else:
            #find parent and delete
            ps.decompose()
    elif ftype=='region':
        #check if at least one is within the region
        in_r = [intersects_poly(xr,yr,cp[0:][::2],cp[1:][::2]) for cp in coords]
        if any(in_r):
            count=+1
        else:
            #find parent and delete
            ps.decompose()
    else:
        print("ftype has to be region or distance")

print('Reduced point sources to {}'.format(count))

##get coordinates
#coords = [p.contents[0].strip().split(' ') for p in positions]
#if ftype=='distance':
#    print('Using distance buffer of {} km around site {},{}'.format(d,xt,yt))
#    #check if these are not close enough to site
#    far = [not(closeby(xt,yt,xs,ys,d)) for xs,ys in coords]
#    #go through positions
#    count=0
#    for p,f in zip(positions,far):
#        #if far:
#        if f:
#            #find parent
#            p.findAllPrevious(name='pointSource')[0].decompose()
#        else:
#            count+=1
#
#elif ftype=='region':
#    print('Using region between {},{} degrees lon and {},{} degrees lat'.format(xr[0],xr[1],yr[0],yr[1]))
#    far = [not(closeby(xt,yt,xs,ys,d)) for xs,ys in coords]
#    #go through positions
#    count=0
#    for p,f in zip(positions,far):
#        #if far:
#        if f:
#            #find parent
#            p.findAllPrevious(name='pointSource')[0].decompose()
#
#print('Reduced point sources to {}'.format(count))

#COMPLEX FAULTS
complex_sources = soup.find_all('complexFaultSource')
print('---\nComplex sources\n---\n'.format(sm))
print('Found {} complex sources'.format(len(complex_sources)))
#go line by line, if any is close keep parent
count=0
for cs in complex_sources:
    positions=cs.find_all('gml:posList')
    #get coordinates
    coords = [p.contents[0].strip().split(' ') for p in positions]
    if ftype=='distance':
        #check if at least one is close enough to site
        close = [closeby(xt,yt,cp[0:][::2],cp[1:][::2],d) for cp in coords]
        if any(close):
            count=+1
        else:
            #find parent and delete
            cs.decompose()
    elif ftype=='region':
        #check if at least one is within the region
        in_r = [intersects_poly(xr,yr,cp[0:][::2],cp[1:][::2]) for cp in coords]
        if any(in_r):
            count=+1
        else:
            #find parent and delete
            cs.decompose()
    else:
        print("ftype has to be region or distance")

print('Reduced complex sources to {}'.format(count))

#FAULT SOURCES
#find all position informations
fault_sources = soup.find_all('simpleFaultSource')

print('---\nSimple line sources\n---\n'.format(sm))
print('Found {} simple line sources'.format(len(fault_sources)))
count=0
for fs in fault_sources:
    positions=fs.find_all('gml:posList')
    #get coordinates
    coords = [p.contents[0].strip().split(' ') for p in positions]
    if ftype=='distance':
        #check if these are not close enough to site
        far = [not(closeby(xt,yt,cp[0:][::2],cp[1:][::2],d)) for cp in coords]
        if any(far):
            fs.decompose()
        else:
            count+=1
    elif ftype=='region':
        #check if at least one is within the region
        in_r = [intersects_poly(xr,yr,cp[0:][::2],cp[1:][::2]) for cp in coords]
        if any(in_r):
            count+=1
        else:
            #find parent and delete
            fs.decompose()
    else:
        print("ftype has to be region or distance")
    #go through positions
    #for p,f in zip(positions,far):
    #    #if far:
    #    if f:
    #        #find parent
    #        p.findAllPrevious(name='simpleFaultSource')[0].decompose()
    #    else:
    #        count+=1

print('Reduced simple fault sources to {}'.format(count))

f = open(output, "w")
f.write(soup.prettify())
f.close()

print('\n### Wrote model to {} ###'.format(output))
