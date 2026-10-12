import numpy as np
def circ(a,b,c):
    ax,ay=a;bx,by=b;cx,cy=c
    d=2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
    ux=((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/d
    uy=((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/d
    o=np.array([ux,uy]); return o, np.linalg.norm(np.array(a)-o)
def inter(p1,p2,q1,q2):
    p1,p2,q1,q2=map(np.array,(p1,p2,q1,q2))
    A=np.array([p2-p1,q1-q2]).T; t=np.linalg.solve(A,q1-p1); return p1+t[0]*(p2-p1)
def foot(p,a,b):
    p,a,b=map(np.array,(p,a,b)); d=b-a; return a+np.dot(p-a,d)/np.dot(d,d)*d
def line_circle(p,d,o,r):
    p,d,o=map(np.array,(p,d,o)); d=d/np.linalg.norm(d)
    b=np.dot(p-o,d); c=np.dot(p-o,p-o)-r*r; s=np.sqrt(b*b-c)
    return p+(-b-s)*d, p+(-b+s)*d
n=np.linalg.norm
def cr(u,v): return u[0]*v[1]-u[1]*v[0]
