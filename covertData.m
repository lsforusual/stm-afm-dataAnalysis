function [ X,Y ] = covertData( data,k,x,y,var)
% ����x�����򣬶����ݽ��д������������
%   Detailed explanation goes here
[row,col]=size(data);
Col_A=data(1:row,1);
Col_B=data(1:row,2);
%������һ�����˼Ӧ����Ҫ����
Col_D=(Col_B-y)/abs(k);
Y=Col_D*var;
X=Col_A-x+Col_D;
%����x��С�������½�������
[new_X,index]=sort(X,'ascend');
new_Y=Y;
for i=1:1:row
    new_Y(i)=Y(index(i));
end
X=new_X;
Y=new_Y;
end

