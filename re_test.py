import re


text = '''<a href="http://www.wenku8.com/wap/userinfo.php?id=15">reika</a>:
3.5、4、5还有那个和文学少女合写的番外都是有爱人士自翻的呢～<br />
催翻译会被雷劈哦～何况就是在这里催站长也没用啊。。。
[2009-03-29]<br/><br/>'''

print(re.findall('<a href=.*[\s\D]*\[[0-9]{4}-[0-9]{2}-[0-9]{2}\]<br/>', text))