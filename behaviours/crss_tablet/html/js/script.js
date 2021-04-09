function hideElement(id)
{
	var x = document.getElementById(id);
	x.style.display = "none";
}

function showElement(id)
{
	var x = document.getElementById(id);
	x.style.display = "inline";
}

function showMain(event)
{
	alert("Hello! I am an alert box!!");
// 	var x = document.getElementById("ttsDiv");
// 	x.style.display = "none";
// 	var x = document.getElementById("imgDiv");
// 	x.style.display = "block";
}

function setText(str) {
	document.getElementById("content").innerHTML = str;
}
