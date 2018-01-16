var rows = document.querySelectorAll(".datadisplaytable tr");
var classes = [];
lastIndex = -1;
for (var i = 0; i < rows.length; i++) {
	var header = rows[i].querySelector(".ddlabel,.ddtitle");
	if (!header) {
		if (lastIndex > -1) {
			var emaillink = rows[i].querySelector('a[href*="mailto"]');
			if (emaillink) {
				classes[lastIndex].prof_name = emaillink.getAttribute("target");
				classes[lastIndex].prof_email = emaillink.getAttribute("href").substr(7);
			} else {
				classes[lastIndex].prof_name = "n/a";
				classes[lastIndex].prof_email = "n/a";
			}
			lastIndex = -1;
		}
		continue;
	}
	var code = header.querySelector("a").innerText;
	var enrollment = rows[i].querySelector("th");
	if (enrollment.querySelector("b")) {
		enrollment = parseInt(enrollment.querySelector("b").innerText.match(/\d+/)[0]);
	} else {
		enrollment = parseInt(enrollment.innerText.split("Enrollment: ")[1].match(/^\d+/)[0]);
	}
	var booksLink = rows[i].querySelector("td a").href.replace(/&amp;/g, "&");
	classes.push({
		code: code.trim(),
		students: enrollment,
		booklist: booksLink,
	});
	lastIndex = classes.length - 1;
}
document.querySelector(".banner_copyright").innerHTML = JSON.stringify(classes);
console.log(classes.length);
"done"
