function filename = fileConv(path,filename)
%ȥ���ı��ļ��е������У�ֻ���������������ݣ�����Distance�У��ڶ��У����ݡ�1E9
%����ֵΪ�µ�filename

fidin = fopen(strcat(path,filename));
tmp=[];
while ~feof(fidin)
    tline=fgetl(fidin);
    if double(tline(1)) >= 48 && double(tline(1)) <= 57
        tmp=[tmp;str2num(tline)];
        continue
    end
end
fclose(fidin);
%ֻ����������������
[row,col]=size(tmp);
if col>2 
    tmp=tmp(:,2:3);
%Distance�����ݡ�1E9
tmp(:,1)=tmp(:,1)*1E9;

%�������ļ�Ϊԭ�ļ���conv.txt
filename=strcat(strcat('Conv_',strtok(filename,'.')),'.txt');
%�����ļ�
save(strcat(path,filename),'tmp','-ascii');
%����ڴ�
clear tmp;
end

