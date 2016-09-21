function pos = maxDistance(Data)
%Ѱ�ҵ��������˵�ȷ����ֱ�ߵľ������ĵ�,���ظõ������

x=[];
y=[];

[row,col]=size(Data);

%��ȡ�����˵�(x1,y1),(x2,y2)
x(1)=Data(1,1);
x(2)=Data(row,1);
y(1)=Data(1,2);
y(2)=Data(row,2);

p=polyfit(x,y,1);%�õ�������ȷ����ֱ��,p(1)��б�ʣ�p(2)�ǳ���
%���㵽ֱ�߾������ĵ�
pos=1;
max=0;
for i=1:1:row
    distance = abs(p(1)*Data(i,1)-Data(i,2)+p(2))/sqrt(p(1)*p(1)+1) ;
    if distance>max
        max=distance;
        pos=i;
    end
end
end

