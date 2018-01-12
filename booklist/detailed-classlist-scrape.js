var emaillinks = document.querySelectorAll('a[href*="mailto"]');
var rows = document.querySelectorAll(".datadisplaytable tr");
var classes = [];
ei = 0;
for (var i = 0; i < rows.length; i++) {
	var header = rows[i].querySelector(".ddlabel,.ddtitle");
	if (!header) {
		continue;
	}
	var name = header.querySelector("a").innerText;
	var enrollment = rows[i].querySelector("th");
	if (enrollment.querySelector("b")) {
		enrollment = parseInt(enrollment.querySelector("b").innerText.match(/\d+/)[0]);
	} else {
		enrollment = parseInt(enrollment.innerText.split("Enrollment: ")[1].match(/^\d+/)[0]);
	}
	var booksLink = rows[i].querySelector("td a").href;
	classes.push({
		name: name.trim(),
		students: enrollment,
		booklist: booksLink,
		prof_name: emaillinks[ei].getAttribute("target"),
		prof_email: emaillinks[ei].getAttribute("href").substr(7),
	});
	ei += 1;
}
document.querySelector(".banner_copyright").innerHTML = JSON.stringify(classes);
"done"
