function [ line1,line2,pos ] = curveFit( Data )
%������ֱ��������ݼ�Data,���عյ���������ڻ�ͼ
[row,col]=size(Data);
data_x=Data(1:row,1);
data_y=Data(1:row,2);

%   ���ȶ�data_x,data_y���н�ά����,������þ��Ȳ�������ÿ��10�������һ��
sample_x = zeros(row/10,1);
sample_y = zeros(row/10,1);

  for i=1:1:row/10
      sample_x(i)=data_x(i*10);
      sample_y(i)=data_y(i*10);
  end
% 
% 
%������Ҫ�ҵ����Ĺյ㣬�����ݷ�Ϊ�����֣��ֱ�����������
pos=maxDistance([sample_x,sample_y]);
pos=pos*10 ;
% 
% part1_x=data_x(1:pos);
% part1_y=data_y(1:pos);
% 
% part2_x=data_x(pos+1:row);
% part2_y=data_y(pos+1:row);

% ��4000�������У�
% �õ�51���㵽��100������������ˮƽֱ�ߣ�

for i=1:1:50
    part1_x(i)=data_x(i+50);
    part1_y(i)=data_y(i+50);
end
% % �õ�1901���㵽��1950��������������һ��ֱ�ߣ�
% % ���������ԭ��1000�㡢2000�����ݵĴ���ʽ��ͬ��
% for i=1:1:50
%     part2_x(i)=data_x(i+1900);
%     part2_y(i)=data_y(i+1900);
% end

% �õ�row-100���㵽��row-50��������������һ��ֱ�ߣ�
% ���������ԭ��1000�㡢2000�����ݵĴ���ʽ��ͬ��
for i=1:1:50
    part2_x(i)=data_x(i+row-100);
    part2_y(i)=data_y(i+row-100);
end


%����������������ݽ������
line1=polyfit(part1_x,part1_y,0);%ֱ��
line2=polyfit(part2_x,part2_y,1);%б��



end

